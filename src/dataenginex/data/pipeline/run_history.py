"""JSON-backed pipeline run history store."""

from __future__ import annotations

import secrets
import threading
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from dataenginex import _json
from dataenginex.data.pipeline.runner import PipelineResult

logger = structlog.get_logger()

__all__ = ["PipelineRunHistory", "PipelineRunRecord"]


@dataclass
class PipelineRunRecord:
    """A single pipeline execution record."""

    run_id: str = field(default_factory=lambda: secrets.token_hex(6))
    pipeline_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    success: bool = False
    rows_input: int = 0
    rows_output: int = 0
    steps_completed: int = 0
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain dict."""
        return asdict(self)


class PipelineRunHistory:
    """Persistent pipeline run history backed by a JSON file."""

    def __init__(self, persist_path: str | Path) -> None:
        self._persist_path = Path(persist_path)
        self._records: list[PipelineRunRecord] = []
        self._lock = threading.Lock()
        if self._persist_path.exists():
            self._load()

    def record(self, result: PipelineResult, duration_ms: float) -> PipelineRunRecord:
        """Record a pipeline execution result."""
        rec = PipelineRunRecord(
            pipeline_name=result.pipeline,
            success=result.success,
            rows_input=result.rows_input,
            rows_output=result.rows_output,
            steps_completed=result.steps_completed,
            duration_ms=round(duration_ms, 2),
            error=result.error,
        )
        with self._lock:
            self._records.append(rec)
            self._save()
        return rec

    def get_runs(self, pipeline_name: str) -> list[PipelineRunRecord]:
        """Get runs for a specific pipeline, newest first."""
        return [r for r in reversed(self._records) if r.pipeline_name == pipeline_name]

    @property
    def all_runs(self) -> list[PipelineRunRecord]:
        """All runs, newest first."""
        return list(reversed(self._records))

    def _save(self) -> None:
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(
            _json.dumps([r.to_dict() for r in self._records], indent=2, default=str)
        )

    def _load(self) -> None:
        try:
            raw = _json.loads(self._persist_path.read_text())
            for item in raw:
                self._records.append(PipelineRunRecord(**item))
        except (ValueError, TypeError, KeyError) as exc:
            logger.warning("run history corrupted, starting fresh", error=str(exc))
            self._records = []
