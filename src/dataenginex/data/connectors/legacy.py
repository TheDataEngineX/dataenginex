"""
Data connectors — abstract interface and concrete implementations.

Every external data source (REST API, file system, message queue) is accessed
through a ``DataConnector`` subclass so that the framework can swap sources
without touching pipeline logic.
"""

from __future__ import annotations

import csv
import io
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()
__all__ = [
    "ConnectorStatus",
    "DataConnector",
    "FetchResult",
    "FileConnector",
    "RestConnector",
]

# ---------------------------------------------------------------------------
# Connector metadata
# ---------------------------------------------------------------------------


class ConnectorStatus(StrEnum):
    """Lifecycle states for a data connector."""

    IDLE = "idle"
    CONNECTED = "connected"
    FETCHING = "fetching"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class FetchResult:
    """Outcome of a single ``fetch`` invocation.

    Attributes:
        records: Retrieved data records.
        record_count: Number of records returned.
        source: Name of the data source.
        fetched_at: Timestamp of the fetch.
        duration_ms: Fetch duration in milliseconds.
        errors: Error messages (empty on success).
    """

    records: list[dict[str, Any]]
    record_count: int
    source: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return ``True`` if the fetch completed without errors."""
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class DataConnector(ABC):
    """Base class for all data connectors in DEX.

    Subclass and implement ``connect``, ``fetch``, and ``close``.
    """

    def __init__(self, name: str, source_type: str) -> None:
        self.name = name
        self.source_type = source_type
        self.status = ConnectorStatus.IDLE
        self._connected_at: datetime | None = None

    # -- lifecycle -----------------------------------------------------------

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the data source."""
        ...

    @abstractmethod
    async def fetch(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> FetchResult:
        """Retrieve records from the data source."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release resources held by the connector."""
        ...

    # -- helpers -------------------------------------------------------------

    def _mark_connected(self) -> None:
        self.status = ConnectorStatus.CONNECTED
        self._connected_at = datetime.now(tz=UTC)
        logger.info("connector connected", name=self.name)

    def _mark_error(self, message: str) -> None:
        self.status = ConnectorStatus.ERROR
        logger.error("connector error", name=self.name, message=message)

    # -- context manager -----------------------------------------------------

    async def __aenter__(self) -> DataConnector:
        await self.connect()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.close()


# ---------------------------------------------------------------------------
# REST connector
# ---------------------------------------------------------------------------


class RestConnector(DataConnector):
    """Fetches records from an HTTP/REST API endpoint.

    Parameters
    ----------
    name:
        Human-readable connector label.
    base_url:
        Root URL of the API (e.g. ``https://api.example.com``).
    endpoint:
        Path appended to *base_url* for fetches (e.g. ``/v1/jobs``).
    headers:
        Extra HTTP headers (auth tokens, accept types, etc.).
    timeout:
        HTTP timeout in seconds (default 30).
    records_key:
        JSON key that contains the result list (e.g. ``"data"``).
        When *None* the root response is expected to be a list.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        endpoint: str = "/",
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        records_key: str | None = "data",
    ) -> None:
        super().__init__(name=name, source_type="rest_api")
        self.base_url = base_url.rstrip("/")
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout = timeout
        self.records_key = records_key
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        """Open an HTTP client session to the configured base URL."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=httpx.Timeout(self.timeout),
            )
            self._mark_connected()
            return True
        except Exception as exc:
            self._mark_error(str(exc))
            return False

    async def fetch(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> FetchResult:
        """Fetch records from the REST endpoint with optional pagination."""
        if self._client is None:
            return FetchResult(
                records=[],
                record_count=0,
                source=self.name,
                errors=["Connector not connected"],
            )

        self.status = ConnectorStatus.FETCHING
        params: dict[str, Any] = {**(filters or {})}
        if limit is not None:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        start = time.perf_counter()
        try:
            resp = await self._client.get(self.endpoint, params=params)
            resp.raise_for_status()
            body = resp.json()

            if self.records_key and isinstance(body, dict):
                records = body.get(self.records_key, [])
            elif isinstance(body, list):
                records = body
            else:
                records = [body]

            duration = (time.perf_counter() - start) * 1000
            self.status = ConnectorStatus.CONNECTED
            return FetchResult(
                records=records,
                record_count=len(records),
                source=self.name,
                duration_ms=round(duration, 2),
            )
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            self._mark_error(str(exc))
            return FetchResult(
                records=[],
                record_count=0,
                source=self.name,
                duration_ms=round(duration, 2),
                errors=[str(exc)],
            )

    async def close(self) -> None:
        """Close the HTTP client session and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self.status = ConnectorStatus.CLOSED
        logger.info("connector closed", name=self.name)


# ---------------------------------------------------------------------------
# File connector (JSON / JSONL / CSV)
# ---------------------------------------------------------------------------


class FileConnector(DataConnector):
    """Reads records from local JSON, JSONL, or CSV files.

    Parameters
    ----------
    name:
        Human-readable connector label.
    path:
        File system path to the data file.
    file_format:
        One of ``"json"``, ``"jsonl"``, ``"csv"``.
    encoding:
        Text encoding (default ``utf-8``).
    """

    SUPPORTED_FORMATS = {"json", "jsonl", "csv"}

    def __init__(
        self,
        name: str,
        path: str | Path,
        file_format: str = "json",
        encoding: str = "utf-8",
    ) -> None:
        super().__init__(name=name, source_type="file")
        self.path = Path(path)
        if file_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format {file_format!r}; choose from {self.SUPPORTED_FORMATS}"
            )
        self.file_format = file_format
        self.encoding = encoding
        self._data: list[dict[str, Any]] | None = None

    async def connect(self) -> bool:
        """Verify the configured file exists and is readable."""
        if not self.path.exists():
            self._mark_error(f"File not found: {self.path}")
            return False
        self._mark_connected()
        return True

    async def fetch(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> FetchResult:
        """Read and parse records from the local file."""
        self.status = ConnectorStatus.FETCHING
        start = time.perf_counter()

        try:
            if self._data is None:
                self._data = self._load()

            records = self._data[offset:]
            if limit is not None:
                records = records[:limit]

            if filters:
                records = [r for r in records if all(r.get(k) == v for k, v in filters.items())]

            duration = (time.perf_counter() - start) * 1000
            self.status = ConnectorStatus.CONNECTED
            return FetchResult(
                records=records,
                record_count=len(records),
                source=self.name,
                duration_ms=round(duration, 2),
            )
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            self._mark_error(str(exc))
            return FetchResult(
                records=[],
                record_count=0,
                source=self.name,
                duration_ms=round(duration, 2),
                errors=[str(exc)],
            )

    async def close(self) -> None:
        """Release cached file data."""
        self._data = None
        self.status = ConnectorStatus.CLOSED

    # -- private loaders -----------------------------------------------------

    def _load(self) -> list[dict[str, Any]]:
        text = self.path.read_text(encoding=self.encoding)
        if self.file_format == "json":
            data = json.loads(text)
            return data if isinstance(data, list) else [data]
        if self.file_format == "jsonl":
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        # csv
        return self._load_csv(text)

    @staticmethod
    def _load_csv(text: str) -> list[dict[str, Any]]:
        reader = csv.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]
