"""
Persistent lineage — JSON-file-backed data lineage tracking.

Records every data movement (ingestion, transformation, enrichment) through
the medallion layers, persisting the graph to disk so it survives restarts.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast, runtime_checkable

import structlog

from dataenginex import _json

logger = structlog.get_logger()
__all__ = [
    "LineageBackend",
    "LineageEvent",
    "PersistentLineage",
    "PostgresLineage",
]


@runtime_checkable
class LineageBackend(Protocol):
    """Structural interface for lineage recording.

    Any object with a ``record(**kwargs)`` method satisfies this Protocol —
    both :class:`PersistentLineage` and ``dataenginex.store.DexStore`` qualify.
    """

    def record(self, **kwargs: Any) -> Any: ...


@dataclass
class LineageEvent:
    """A single lineage event describing a data operation.

    Attributes:
        event_id: Auto-generated unique identifier (12-char hex).
        parent_id: ID of the upstream event that produced the input.
        operation: Type of operation (``"ingest"``, ``"transform"``, ``"enrich"``, ``"export"``).
        layer: Medallion layer (``"bronze"``, ``"silver"``, ``"gold"``).
        source: Where data came from.
        destination: Where data was written.
        input_count: Number of input records.
        output_count: Number of output records.
        error_count: Number of records that errored.
        quality_score: Quality score of the output (0.0–1.0).
        pipeline_name: Name of the owning pipeline.
        step_name: Name of the transform step.
        metadata: Free-form context dict.
        timestamp: When the event occurred.
    """

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: str | None = None

    # What happened
    operation: str = ""  # "ingest", "transform", "enrich", "export"
    layer: str = ""  # "bronze", "silver", "gold"
    source: str = ""
    destination: str = ""

    # Counts
    input_count: int = 0
    output_count: int = 0
    error_count: int = 0
    quality_score: float | None = None

    # Context
    pipeline_name: str = ""
    step_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the lineage event to a plain dictionary."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


class PersistentLineage:
    """JSON-file-backed lineage store.

    Example::

        lineage = PersistentLineage("data/lineage.json")
        ev = lineage.record(
            operation="ingest",
            layer="bronze",
            source="linkedin",
            input_count=1250,
            output_count=1250,
        )
        # later
        lineage.record(
            operation="transform",
            layer="silver",
            parent_id=ev.event_id,
            input_count=1250,
            output_count=1200,
            quality_score=0.88,
        )
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        self._events: list[LineageEvent] = []
        self._persist_path = Path(persist_path) if persist_path else None
        self._lock = threading.Lock()
        if self._persist_path and self._persist_path.exists():
            self._load()

    # -- public API ----------------------------------------------------------

    def record(self, **kwargs: Any) -> LineageEvent:
        """Create and store a new lineage event.

        Accepts the same keyword arguments as ``LineageEvent``.
        """
        with self._lock:
            event = LineageEvent(**kwargs)
            self._events.append(event)
            logger.info(
                "Lineage event %s: %s %s → %s (%d→%d)",
                event.event_id,
                event.operation,
                event.source,
                event.destination,
                event.input_count,
                event.output_count,
            )
            self._save()
        return event

    def get_event(self, event_id: str) -> LineageEvent | None:
        """Fetch a single event by ID."""
        for ev in self._events:
            if ev.event_id == event_id:
                return ev
        return None

    def get_children(self, parent_id: str) -> list[LineageEvent]:
        """Return events that have *parent_id* as their parent."""
        return [ev for ev in self._events if ev.parent_id == parent_id]

    def get_chain(self, event_id: str) -> list[LineageEvent]:
        """Walk up from *event_id* to the root and return the full chain."""
        chain: list[LineageEvent] = []
        current = self.get_event(event_id)
        while current:
            chain.append(current)
            current = self.get_event(current.parent_id) if current.parent_id else None
        chain.reverse()
        return chain

    def get_by_layer(self, layer: str) -> list[LineageEvent]:
        """Return all events for a given medallion layer."""
        return [ev for ev in self._events if ev.layer == layer]

    def get_by_pipeline(self, pipeline_name: str) -> list[LineageEvent]:
        """Return all events for a given pipeline."""
        return [ev for ev in self._events if ev.pipeline_name == pipeline_name]

    @property
    def all_events(self) -> list[LineageEvent]:
        """Return a shallow copy of all stored lineage events."""
        return list(self._events)

    def summary(self) -> dict[str, Any]:
        """Return high-level lineage statistics."""
        layers: dict[str, int] = {}
        operations: dict[str, int] = {}
        for ev in self._events:
            layers[ev.layer] = layers.get(ev.layer, 0) + 1
            operations[ev.operation] = operations.get(ev.operation, 0) + 1
        return {
            "total_events": len(self._events),
            "by_layer": layers,
            "by_operation": operations,
        }

    # -- persistence ---------------------------------------------------------

    def _save(self) -> None:
        if not self._persist_path:
            return
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = [ev.to_dict() for ev in self._events]
        self._persist_path.write_text(_json.dumps(data, indent=2, default=str))

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            raw = _json.loads(self._persist_path.read_text())
            for item in raw:
                item.pop("timestamp", None)
                self._events.append(LineageEvent(**item))
            logger.info(
                "lineage events loaded",
                count=len(self._events),
                path=str(self._persist_path),
            )
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning(
                "lineage file corrupted, starting fresh",
                path=str(self._persist_path),
                error=str(exc),
            )
            self._events = []


class PostgresLineage:
    """PostgreSQL-backed lineage store for production deployments.

    Stores lineage events in a ``lineage_events`` table.  Requires
    ``asyncpg`` and ``DEX_DATABASE_URL``.  Falls back to
    :class:`PersistentLineage` (JSON file) when the database is
    unavailable so the API starts even without PostgreSQL.

    Table schema (auto-created)::

        CREATE TABLE IF NOT EXISTS lineage_events (
            event_id      TEXT PRIMARY KEY,
            parent_id     TEXT,
            operation     TEXT,
            layer         TEXT,
            source        TEXT,
            destination   TEXT,
            input_count   INTEGER,
            output_count  INTEGER,
            error_count   INTEGER,
            quality_score DOUBLE PRECISION,
            pipeline_name TEXT,
            step_name     TEXT,
            metadata      JSONB,
            timestamp     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS lineage_events (
            event_id      TEXT PRIMARY KEY,
            parent_id     TEXT,
            operation     TEXT NOT NULL DEFAULT '',
            layer         TEXT NOT NULL DEFAULT '',
            source        TEXT NOT NULL DEFAULT '',
            destination   TEXT NOT NULL DEFAULT '',
            input_count   INTEGER NOT NULL DEFAULT 0,
            output_count  INTEGER NOT NULL DEFAULT 0,
            error_count   INTEGER NOT NULL DEFAULT 0,
            quality_score DOUBLE PRECISION,
            pipeline_name TEXT NOT NULL DEFAULT '',
            step_name     TEXT NOT NULL DEFAULT '',
            metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
            timestamp     TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_lineage_pipeline ON lineage_events(pipeline_name);
        CREATE INDEX IF NOT EXISTS idx_lineage_layer    ON lineage_events(layer);
        CREATE INDEX IF NOT EXISTS idx_lineage_parent   ON lineage_events(parent_id);
    """

    def __init__(self, dsn: str, fallback_path: str | Path | None = None) -> None:
        self._dsn = dsn
        self._fallback = PersistentLineage(fallback_path)
        self._pg_ok = False
        try:
            self._run(self._ensure_table())
            self._pg_ok = True
        except ImportError as exc:
            logger.warning(
                "asyncpg not installed — using JSON fallback for lineage. "
                "Install via: pip install 'dataenginex[postgres]'",
                error=str(exc),
            )
        except Exception as exc:
            logger.warning("postgres lineage unavailable, using JSON fallback", error=str(exc))

    async def _ensure_table(self) -> None:
        import asyncpg

        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(self._CREATE_TABLE)
        finally:
            await conn.close()

    def _run(self, coro: Any) -> Any:
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, coro).result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def record(self, **kwargs: Any) -> LineageEvent:
        """Persist a new lineage event to PostgreSQL (or JSON fallback)."""
        event = LineageEvent(**kwargs)
        if not self._pg_ok:
            return self._fallback.record(**kwargs)
        self._run(self._ainsert(event))
        logger.info(
            "lineage.record",
            event_id=event.event_id,
            operation=event.operation,
            source=event.source,
            destination=event.destination,
        )
        return event

    async def _ainsert(self, ev: LineageEvent) -> None:
        import asyncpg

        conn = await asyncpg.connect(self._dsn)
        try:
            await conn.execute(
                """INSERT INTO lineage_events
                   (event_id, parent_id, operation, layer, source, destination,
                    input_count, output_count, error_count, quality_score,
                    pipeline_name, step_name, metadata, timestamp)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14)
                   ON CONFLICT (event_id) DO NOTHING""",
                ev.event_id,
                ev.parent_id,
                ev.operation,
                ev.layer,
                ev.source,
                ev.destination,
                ev.input_count,
                ev.output_count,
                ev.error_count,
                ev.quality_score,
                ev.pipeline_name,
                ev.step_name,
                _json.dumps(ev.metadata),
                ev.timestamp,
            )
        finally:
            await conn.close()

    def _row_to_event(self, row: Any) -> LineageEvent:
        raw_meta = row["metadata"]
        meta: dict[str, Any] = (
            _json.loads(raw_meta) if isinstance(raw_meta, str) else dict(raw_meta or {})
        )
        return LineageEvent(
            event_id=row["event_id"],
            parent_id=row["parent_id"],
            operation=row["operation"],
            layer=row["layer"],
            source=row["source"],
            destination=row["destination"],
            input_count=row["input_count"],
            output_count=row["output_count"],
            error_count=row["error_count"],
            quality_score=row["quality_score"],
            pipeline_name=row["pipeline_name"],
            step_name=row["step_name"],
            metadata=meta,
            timestamp=row["timestamp"],
        )

    async def _afetch(self, sql: str, *args: Any) -> list[LineageEvent]:
        import asyncpg

        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(sql, *args)
            return [self._row_to_event(r) for r in rows]
        finally:
            await conn.close()

    def get_event(self, event_id: str) -> LineageEvent | None:
        if not self._pg_ok:
            return self._fallback.get_event(event_id)
        results = self._run(
            self._afetch("SELECT * FROM lineage_events WHERE event_id=$1", event_id)
        )
        return results[0] if results else None

    def get_children(self, parent_id: str) -> list[LineageEvent]:
        if not self._pg_ok:
            return self._fallback.get_children(parent_id)
        return cast(
            list[LineageEvent],
            self._run(
                self._afetch(
                    "SELECT * FROM lineage_events WHERE parent_id=$1 ORDER BY timestamp", parent_id
                )
            ),
        )

    def get_chain(self, event_id: str) -> list[LineageEvent]:
        if not self._pg_ok:
            return self._fallback.get_chain(event_id)
        chain: list[LineageEvent] = []
        current = self.get_event(event_id)
        while current:
            chain.append(current)
            current = self.get_event(current.parent_id) if current.parent_id else None
        chain.reverse()
        return chain

    def get_by_layer(self, layer: str) -> list[LineageEvent]:
        if not self._pg_ok:
            return self._fallback.get_by_layer(layer)
        return cast(
            list[LineageEvent],
            self._run(
                self._afetch(
                    "SELECT * FROM lineage_events WHERE layer=$1 ORDER BY timestamp DESC", layer
                )
            ),
        )

    def get_by_pipeline(self, pipeline_name: str) -> list[LineageEvent]:
        if not self._pg_ok:
            return self._fallback.get_by_pipeline(pipeline_name)
        return cast(
            list[LineageEvent],
            self._run(
                self._afetch(
                    "SELECT * FROM lineage_events WHERE pipeline_name=$1 ORDER BY timestamp DESC",
                    pipeline_name,
                )
            ),
        )

    @property
    def all_events(self) -> list[LineageEvent]:
        if not self._pg_ok:
            return self._fallback.all_events
        return self._run(  # type: ignore[no-any-return]
            self._afetch("SELECT * FROM lineage_events ORDER BY timestamp DESC LIMIT 1000")
        )

    def summary(self) -> dict[str, Any]:
        if not self._pg_ok:
            return self._fallback.summary()
        return self._run(self._asummary())  # type: ignore[no-any-return]

    async def _asummary(self) -> dict[str, Any]:
        import asyncpg

        conn = await asyncpg.connect(self._dsn)
        try:
            total = await conn.fetchval("SELECT COUNT(*) FROM lineage_events")
            layer_rows = await conn.fetch(
                "SELECT layer, COUNT(*) as n FROM lineage_events GROUP BY layer"
            )
            op_rows = await conn.fetch(
                "SELECT operation, COUNT(*) as n FROM lineage_events GROUP BY operation"
            )
        finally:
            await conn.close()
        return {
            "total_events": total,
            "by_layer": {r["layer"]: r["n"] for r in layer_rows},
            "by_operation": {r["operation"]: r["n"] for r in op_rows},
        }
