"""HTTP connector — downloads remote tabular files and caches them locally.

Supports TSV/CSV files (optionally gzip-compressed) from any HTTPS URL.
Designed for IMDB Non-Commercial Datasets but works with any URL that
returns a delimited text file.

On every ``connect()`` call the connector checks the cache age:
- If the cached parquet is younger than ``max_age_hours`` (default 20h), it
  is reused — no network request.
- Otherwise the file is re-downloaded, decompressed on-the-fly, and
  converted to Snappy Parquet via DuckDB.

``read()`` returns a ``pyarrow.Table`` so the PipelineRunner can register it
directly in DuckDB without a costly Python-object round-trip.
"""

from __future__ import annotations

import gzip
import shutil
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import duckdb
import pyarrow.parquet as pq
import structlog

from dataenginex.core.interfaces import BaseConnector
from dataenginex.data.connectors import connector_registry

logger = structlog.get_logger()

_DEFAULT_CACHE_DIR = Path.home() / ".dex" / "cache"
_DEFAULT_MAX_AGE_H = 20  # re-download if cached file is older than this


@connector_registry.decorator("http")
class HttpConnector(BaseConnector):
    """HTTP connector for remote delimited files (TSV/CSV, optionally gzipped).

    Args:
        url: Full URL to the remote file (e.g. https://datasets.imdbws.com/title.basics.tsv.gz).
        cache_dir: Directory for the local parquet cache. Defaults to ~/.dex/cache/.
        sep: Field separator (default ``\\t`` for TSV).
        null_str: String representing NULL in the source file (default ``\\N`` for IMDB).
        max_age_hours: Hours before the cache is considered stale (default 20).
        all_varchar: Read all columns as strings to avoid type-inference failures (default True).
    """

    def __init__(
        self,
        url: str,
        cache_dir: str | None = None,
        sep: str = "\t",
        null_str: str = "\\N",
        max_age_hours: float = _DEFAULT_MAX_AGE_H,
        all_varchar: bool = True,
        **kwargs: Any,
    ) -> None:
        self._url = url
        self._cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
        self._sep = sep
        self._null_str = null_str
        self._max_age_secs = max_age_hours * 3600
        self._all_varchar = all_varchar
        self._cached_parquet: Path | None = None

    # ── Cache path ────────────────────────────────────────────────────────────

    def _cache_path(self) -> Path:
        """Derive a stable cache filename from the URL."""
        import hashlib

        stem = Path(self._url.split("?")[0]).stem  # e.g. "title.basics" from .tsv.gz
        stem = stem.replace(".", "_")  # → title_basics
        url_hash = hashlib.sha1(self._url.encode()).hexdigest()[:8]
        return self._cache_dir / f"{stem}_{url_hash}.parquet"

    def _is_cache_fresh(self, path: Path) -> bool:
        if not path.exists():
            return False
        age = time.time() - path.stat().st_mtime
        return age < self._max_age_secs

    # ── Download + convert ────────────────────────────────────────────────────

    def _download_and_convert(self, dest: Path) -> None:
        """Stream-download the URL, decompress if gzipped, convert to Parquet."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        is_gz = self._url.endswith(".gz")

        logger.info("http connector downloading", url=self._url, dest=str(dest))
        t0 = time.monotonic()

        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "download.raw"

            with urllib.request.urlopen(self._url, timeout=300) as resp, open(raw_path, "wb") as f:
                shutil.copyfileobj(resp, f)

            # Decompress gzip to a plain TSV so DuckDB can read it without
            # needing to decompress multiple times during conversion.
            if is_gz:
                tsv_path = Path(tmp) / "data.tsv"
                with gzip.open(raw_path, "rb") as f_in, tsv_path.open("wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            else:
                tsv_path = raw_path

            tmp_dest = dest.with_suffix(".tmp.parquet")
            sep_escaped = self._sep.replace("'", "''")
            null_escaped = self._null_str.replace("'", "''")
            tsv_str = str(tsv_path).replace("'", "''")
            out_str = str(tmp_dest).replace("'", "''")

            con = duckdb.connect(":memory:")
            try:
                varchar_clause = ", all_varchar=true" if self._all_varchar else ""
                con.execute(f"""
                    COPY (
                        SELECT * FROM read_csv(
                            '{tsv_str}',
                            sep='{sep_escaped}',
                            header=true,
                            nullstr='{null_escaped}',
                            ignore_errors=true{varchar_clause}
                        )
                    )
                    TO '{out_str}' (FORMAT PARQUET, COMPRESSION SNAPPY)
                """)
                row = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_str}')").fetchone()
                rows = int(row[0]) if row else 0
            finally:
                con.close()

            tmp_dest.rename(dest)

        elapsed = time.monotonic() - t0
        size_mb = dest.stat().st_size / 1_048_576
        logger.info(
            "http connector cached",
            url=self._url,
            rows=rows,
            size_mb=round(size_mb, 1),
            elapsed_s=round(elapsed, 1),
        )

    # ── BaseConnector ─────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Ensure the local parquet cache is fresh, downloading if needed."""
        path = self._cache_path()
        if self._is_cache_fresh(path):
            logger.info("http connector using cache", path=str(path))
        else:
            self._download_and_convert(path)
        self._cached_parquet = path

    def disconnect(self) -> None:
        self._cached_parquet = None

    def read(
        self,
        *,
        table: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Return the cached data as a ``pyarrow.Table``.

        The PipelineRunner registers this directly in DuckDB —
        no Python-level row iteration needed.
        """
        if self._cached_parquet is None or not self._cached_parquet.exists():
            msg = "HttpConnector not connected — call connect() first"
            raise RuntimeError(msg)
        tbl = pq.read_table(str(self._cached_parquet))  # type: ignore[no-untyped-call]
        logger.info("http connector read", rows=len(tbl), path=str(self._cached_parquet))
        return tbl

    def write(self, data: Any, *, table: str = "", **kwargs: Any) -> None:
        raise NotImplementedError("HttpConnector is read-only")

    def health_check(self) -> bool:
        path = self._cache_path()
        return path.exists()
