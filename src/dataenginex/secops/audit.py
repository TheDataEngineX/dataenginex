"""SecOps audit logging — structured log of PII detection and masking operations.

Every time PII is detected or masked, an ``AuditEvent`` is emitted via
structlog (structured key-value format) and persisted via the configured
backend (SQLite WAL by default).

This is NOT a replacement for a production audit trail (e.g. SIEM).
It is a lightweight in-process layer that makes PII handling observable
and testable without external infrastructure.

Thread-safety: SQLite WAL mode with per-thread connections.  Multiple
threads in dex-studio's web server can call ``AuditLogger.log()``
concurrently without races.  The previous DuckDB backend had an explicit
"not thread-safe" disclaimer and a racy ``_seq`` integer counter.
"""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog

from dataenginex import _json

logger = structlog.get_logger()

__all__ = [
    "AuditEvent",
    "AuditLogger",
    "AuditOperation",
]

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS audit_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    operation    TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    pii_fields   TEXT NOT NULL,
    record_count INTEGER NOT NULL,
    actor        TEXT NOT NULL,
    metadata     TEXT NOT NULL,
    occurred_at  TEXT NOT NULL
)
"""

_INSERT = """
INSERT INTO audit_events
    (operation, dataset_name, pii_fields, record_count, actor, metadata, occurred_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

_EVICT = """
DELETE FROM audit_events
WHERE id NOT IN (
    SELECT id FROM audit_events ORDER BY id DESC LIMIT ?
)
"""


class AuditOperation(StrEnum):
    """Type of SecOps operation being logged."""

    PII_SCAN = "pii_scan"
    PII_MASK = "pii_mask"
    PII_ACCESS = "pii_access"


@dataclass(frozen=True)
class AuditEvent:
    """A single audit log entry.

    Attributes:
        operation: Type of operation performed.
        dataset_name: Logical name of the dataset processed.
        pii_fields: Field names identified or masked.
        record_count: Number of records processed.
        actor: System component or user that triggered the operation.
        metadata: Extra context (strategy used, confidence scores, etc.).
        occurred_at: Timestamp of the event.
    """

    operation: AuditOperation
    dataset_name: str
    pii_fields: list[str]
    record_count: int
    actor: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the event to a plain dictionary."""
        return {
            "operation": self.operation.value,
            "dataset_name": self.dataset_name,
            "pii_fields": self.pii_fields,
            "record_count": self.record_count,
            "actor": self.actor,
            "metadata": self.metadata,
            "occurred_at": self.occurred_at.isoformat(),
        }


class _SQLiteAuditBackend:
    """SQLite WAL-backed audit store — thread-safe, multi-process-safe."""

    def __init__(self, db_path: str, max_history: int) -> None:
        self._db_path = db_path
        self._max = max_history
        self._in_memory = db_path == ":memory:"
        self._lock = threading.Lock()

        if self._in_memory:
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            with self._mem_conn:
                self._mem_conn.execute(_CREATE_TABLE)
        else:
            self._tls: threading.local = threading.local()
            with self._get_conn() as conn:
                conn.execute(_CREATE_TABLE)

    def _get_conn(self) -> sqlite3.Connection:
        if self._in_memory:
            return self._mem_conn
        if not hasattr(self._tls, "conn") or self._tls.conn is None:
            conn = sqlite3.connect(self._db_path, timeout=10.0, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._tls.conn = conn
        return self._tls.conn  # type: ignore[no-any-return]

    def append(self, event: AuditEvent) -> None:
        # AUTOINCREMENT — no _seq counter, no race condition
        with self._lock, self._get_conn() as conn:
            conn.execute(
                _INSERT,
                [
                    event.operation.value,
                    event.dataset_name,
                    _json.dumps(event.pii_fields),
                    event.record_count,
                    event.actor,
                    _json.dumps(event.metadata),
                    event.occurred_at.isoformat(),
                ],
            )
            conn.execute(_EVICT, [self._max])

    def all(self) -> list[AuditEvent]:
        rows = (
            self._get_conn()
            .execute(
                "SELECT operation, dataset_name, pii_fields, record_count, "
                "actor, metadata, occurred_at "
                "FROM audit_events ORDER BY id ASC"
            )
            .fetchall()
        )
        return [self._row_to_event(r) for r in rows]

    def filter_by_dataset(self, dataset_name: str) -> list[AuditEvent]:
        rows = (
            self._get_conn()
            .execute(
                "SELECT operation, dataset_name, pii_fields, record_count, "
                "actor, metadata, occurred_at "
                "FROM audit_events WHERE dataset_name = ? ORDER BY id ASC",
                [dataset_name],
            )
            .fetchall()
        )
        return [self._row_to_event(r) for r in rows]

    def clear(self) -> None:
        with self._lock, self._get_conn() as conn:
            conn.execute("DELETE FROM audit_events")

    def close(self) -> None:
        if self._in_memory:
            self._mem_conn.close()
        elif hasattr(self._tls, "conn") and self._tls.conn is not None:
            self._tls.conn.close()
            self._tls.conn = None

    @staticmethod
    def _row_to_event(row: tuple[Any, ...]) -> AuditEvent:
        pii_fields: list[str] = [str(x) for x in _json.loads(row[2])]
        meta: dict[str, Any] = _json.loads(row[5])
        return AuditEvent(
            operation=AuditOperation(row[0]),
            dataset_name=row[1],
            pii_fields=pii_fields,
            record_count=int(row[3]),
            actor=row[4],
            metadata=meta,
            occurred_at=datetime.fromisoformat(row[6]),
        )


class AuditLogger:
    """Audit log for SecOps operations backed by SQLite WAL.

    Emits structured structlog events on every write and persists events
    in a SQLite database (in-memory by default, file-backed when *db_path*
    is a filesystem path).

    Thread-safe: WAL mode + per-thread connections.  Multiple web-server
    workers can call ``log()`` concurrently without corruption.

    Parameters
    ----------
    max_history:
        Maximum number of events to retain (FIFO eviction by insertion order).
    db_path:
        SQLite database path. Defaults to ``":memory:"`` (no persistence).
        Pass a file path (e.g. ``"/var/lib/dex/audit.db"``) for persistence
        across restarts.
    """

    def __init__(self, max_history: int = 1000, db_path: str = ":memory:") -> None:
        self._backend = _SQLiteAuditBackend(db_path, max_history)

    def log(self, event: AuditEvent) -> None:
        """Record an audit event (backend + structlog)."""
        self._backend.append(event)
        logger.info(
            "secops audit event",
            operation=event.operation.value,
            dataset=event.dataset_name,
            pii_fields=event.pii_fields,
            record_count=event.record_count,
            actor=event.actor,
            **{k: v for k, v in event.metadata.items() if isinstance(v, (str, int, float, bool))},
        )

    def log_scan(
        self,
        dataset_name: str,
        pii_fields: list[str],
        record_count: int,
        actor: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Convenience method to log a PII scan operation."""
        event = AuditEvent(
            operation=AuditOperation.PII_SCAN,
            dataset_name=dataset_name,
            pii_fields=pii_fields,
            record_count=record_count,
            actor=actor,
            metadata=metadata or {},
        )
        self.log(event)
        return event

    def log_mask(
        self,
        dataset_name: str,
        pii_fields: list[str],
        record_count: int,
        strategy: str,
        actor: str = "system",
    ) -> AuditEvent:
        """Convenience method to log a PII masking operation."""
        event = AuditEvent(
            operation=AuditOperation.PII_MASK,
            dataset_name=dataset_name,
            pii_fields=pii_fields,
            record_count=record_count,
            actor=actor,
            metadata={"strategy": strategy},
        )
        self.log(event)
        return event

    @property
    def events(self) -> list[AuditEvent]:
        """Return all retained audit events (oldest first)."""
        return self._backend.all()

    def events_for(self, dataset_name: str) -> list[AuditEvent]:
        """Return all events for a specific dataset."""
        return self._backend.filter_by_dataset(dataset_name)

    def clear(self) -> None:
        """Clear all retained events."""
        self._backend.clear()

    def close(self) -> None:
        """Release the SQLite connection. Important for file-backed databases."""
        self._backend.close()

    def __del__(self) -> None:
        import contextlib  # noqa: PLC0415

        with contextlib.suppress(Exception):
            self.close()
