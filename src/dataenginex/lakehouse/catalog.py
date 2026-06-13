"""Data catalog — registry of lakehouse datasets with metadata.

DataCatalog is a thin facade over DexStore (SQLite). All persistence is
delegated to DexStore, which provides WAL-mode thread safety and
multi-process safety with no extra locking required here.

This eliminates the previous JSON-file backing and its associated
race conditions (no lock, non-atomic writes, timestamps lost on reload).

Constructor signatures (all backward-compatible):
  DataCatalog()                        — in-memory (tests, one-shot scripts)
  DataCatalog(persist_path=path)       — dedicated SQLite file at *path*
  DataCatalog(store=existing_store)    — share the engine's DexStore (no split-brain)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from dataenginex.store import DexStore

logger = structlog.get_logger()

__all__ = [
    "CatalogEntry",
    "DataCatalog",
]


@dataclass
class CatalogEntry:
    """Metadata about a single dataset in the lakehouse.

    Attributes:
        name: Unique dataset name.
        layer: Medallion layer (``"bronze"``, ``"silver"``, ``"gold"``).
        format: Storage format (``"parquet"``, ``"json"``, ``"delta"``).
        location: File path or table reference.
        record_count: Approximate number of records.
        schema_fields: List of column/field names.
        description: Human-readable dataset description.
        owner: Team or user responsible for the dataset.
        tags: Arbitrary labels for discovery.
        created_at: When the dataset was first registered.
        updated_at: When the entry was last updated.
        metadata: Free-form context dict.
        version: Auto-incremented version counter.
    """

    name: str
    layer: str  # "bronze", "silver", "gold"
    format: str  # "parquet", "json", "delta"
    location: str
    record_count: int = 0
    schema_fields: list[str] = field(default_factory=list)
    description: str = ""
    owner: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d


class DataCatalog:
    """Lakehouse dataset catalog backed by SQLite via DexStore.

    All writes are ACID and thread-safe. Multiple processes (CLI + web server)
    can use the same catalog file simultaneously without corruption.

    Args:
        persist_path: Path for a dedicated SQLite catalog file.
        store: Existing DexStore to share — avoids a second DB file and
               eliminates the split-brain between catalog and store state.
    """

    def __init__(
        self,
        persist_path: str | Path | None = None,
        *,
        store: DexStore | None = None,
    ) -> None:
        from dataenginex.store import DexStore as _DexStore

        if store is not None:
            self._store = store
            self._owns_store = False
        elif persist_path is not None:
            self._store = _DexStore(Path(persist_path))
            self._owns_store = True
        else:
            self._store = _DexStore(Path(":memory:"))
            self._owns_store = True

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def register(self, entry: CatalogEntry) -> CatalogEntry:
        """Register or update a dataset entry."""
        result = self._store.register_catalog(self._to_store(entry))
        return self._from_store(result)

    def get(self, name: str) -> CatalogEntry | None:
        """Retrieve an entry by name."""
        row = self._store.get_catalog(name)
        return self._from_store(row) if row else None

    def search(
        self,
        *,
        layer: str | None = None,
        tags: list[str] | None = None,
        owner: str | None = None,
        name_contains: str | None = None,
    ) -> list[CatalogEntry]:
        """Search entries by criteria.

        ``tags`` and ``owner`` filters are applied in-memory after the SQL
        query (SQLite JSON array filtering is not used for portability).
        """
        rows = self._store.search_catalog(layer=layer, name_contains=name_contains)
        results = [self._from_store(r) for r in rows]
        if tags:
            tag_set = set(tags)
            results = [e for e in results if tag_set.issubset(set(e.tags))]
        if owner:
            results = [e for e in results if e.owner == owner]
        return results

    def list_all(self) -> list[CatalogEntry]:
        """Return all catalog entries."""
        return [self._from_store(r) for r in self._store.all_catalog()]

    def delete(self, name: str) -> bool:
        """Remove an entry by name."""
        if self._store.get_catalog(name) is None:
            return False
        self._store._write("DELETE FROM catalog_entries WHERE name=?", [name])
        return True

    def summary(self) -> dict[str, Any]:
        """High-level catalog statistics."""
        entries = self.list_all()
        layers: dict[str, int] = {}
        formats: dict[str, int] = {}
        for e in entries:
            layers[e.layer] = layers.get(e.layer, 0) + 1
            formats[e.format] = formats.get(e.format, 0) + 1
        return {
            "total_datasets": len(entries),
            "by_layer": layers,
            "by_format": formats,
        }

    def close(self) -> None:
        if self._owns_store:
            self._store.close()

    # -------------------------------------------------------------------------
    # Type bridge: catalog.CatalogEntry <-> store.CatalogEntry
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_store(entry: CatalogEntry) -> Any:
        from dataenginex.store import CatalogEntry as _SE

        return _SE(
            name=entry.name,
            layer=entry.layer,
            format=entry.format,
            location=entry.location,
            record_count=entry.record_count,
            schema_fields=list(entry.schema_fields),
            description=entry.description,
            owner=entry.owner,
            tags=list(entry.tags),
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            metadata=dict(entry.metadata),
            version=entry.version,
        )

    @staticmethod
    def _from_store(row: Any) -> CatalogEntry:
        return CatalogEntry(
            name=row.name,
            layer=row.layer,
            format=row.format,
            location=row.location,
            record_count=row.record_count,
            schema_fields=list(row.schema_fields),
            description=row.description,
            owner=row.owner,
            tags=list(row.tags),
            created_at=row.created_at,
            updated_at=row.updated_at,
            metadata=dict(row.metadata),
            version=row.version,
        )
