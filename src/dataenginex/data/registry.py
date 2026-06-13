"""
Schema registry — versioned schema management for DEX datasets.

Stores schema definitions (as JSON-serialisable dicts) with
semantic versioning, allowing pipelines to validate data against
a specific schema revision and to track schema evolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from dataenginex import _json

logger = structlog.get_logger()
__all__ = [
    "SchemaRegistry",
    "SchemaVersion",
]


@dataclass
class SchemaVersion:
    """An immutable snapshot of a schema at a particular version.

    Attributes:
        name: Schema identifier (e.g. ``"user_event"``).
        version: Semver string (e.g. ``"1.2.0"``).
        fields: Mapping of field names to type descriptions.
        required_fields: Fields that must be present in every record.
        description: Human-readable summary of the schema.
        created_at: When this version was registered.
        metadata: Extra context dict.
    """

    name: str
    version: str  # semver string, e.g. "1.2.0"
    fields: dict[str, str]  # field_name → type_description
    required_fields: list[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the schema version to a plain dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "fields": self.fields,
            "required_fields": self.required_fields,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    def validate_record(self, record: dict[str, Any]) -> tuple[bool, list[str]]:
        """Check that *record* has all required fields.

        Returns ``(is_valid, errors)`` where *errors* lists the missing
        required fields.
        """
        missing = [f for f in self.required_fields if f not in record]
        return len(missing) == 0, [f"Missing required field: {f}" for f in missing]


class SchemaRegistry:
    """In-process schema registry backed by an optional JSON file.

    Parameters
    ----------
    persist_path:
        If given, schemas are saved/loaded from this JSON file so they
        survive across process restarts.
    """

    def __init__(self, persist_path: str | Path | None = None) -> None:
        # schema_name → [SchemaVersion …] (ordered oldest → newest)
        self._schemas: dict[str, list[SchemaVersion]] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path and self._persist_path.exists():
            self._load()

    # -- public API ----------------------------------------------------------

    def register(self, schema: SchemaVersion) -> SchemaVersion:
        """Register a new schema version.  Duplicate versions are rejected."""
        versions = self._schemas.setdefault(schema.name, [])
        existing = {v.version for v in versions}
        if schema.version in existing:
            raise ValueError(f"Schema {schema.name!r} version {schema.version} already registered")
        versions.append(schema)
        logger.info("schema registered", name=schema.name, version=schema.version)
        self._save()
        return schema

    def get_latest(self, name: str) -> SchemaVersion | None:
        """Return the most recently registered version for *name*."""
        versions = self._schemas.get(name)
        if not versions:
            return None
        return versions[-1]

    def get_version(self, name: str, version: str) -> SchemaVersion | None:
        """Return a specific version, or *None* if not found."""
        for v in self._schemas.get(name, []):
            if v.version == version:
                return v
        return None

    def list_schemas(self) -> list[str]:
        """Return all registered schema names."""
        return list(self._schemas.keys())

    def list_versions(self, name: str) -> list[str]:
        """Return all registered versions for *name* (oldest first)."""
        return [v.version for v in self._schemas.get(name, [])]

    def validate(
        self, name: str, record: dict[str, Any], version: str | None = None
    ) -> tuple[bool, list[str]]:
        """Validate *record* against a schema.

        If *version* is ``None`` the latest version is used.
        """
        schema = self.get_version(name, version) if version else self.get_latest(name)
        if schema is None:
            return False, [f"Schema {name!r} (version={version}) not found"]
        return schema.validate_record(record)

    # -- persistence ---------------------------------------------------------

    def _save(self) -> None:
        if not self._persist_path:
            return
        data: dict[str, list[dict[str, Any]]] = {}
        for name, versions in self._schemas.items():
            data[name] = [v.to_dict() for v in versions]
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(_json.dumps(data, indent=2, default=str))

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        raw = _json.loads(self._persist_path.read_text())
        for name, versions in raw.items():
            self._schemas[name] = [
                SchemaVersion(
                    name=v["name"],
                    version=v["version"],
                    fields=v["fields"],
                    required_fields=v.get("required_fields", []),
                    description=v.get("description", ""),
                    metadata=v.get("metadata", {}),
                )
                for v in versions
            ]
        logger.info("schemas loaded", count=len(self._schemas), path=str(self._persist_path))
