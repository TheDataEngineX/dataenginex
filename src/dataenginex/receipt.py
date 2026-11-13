"""Versioned run receipts (decision 0008).

A receipt is an OpenLineage-shaped superset: run, job and facets,
plus DataEngineX facets - rows per layer table, quality results, and
cost fields (zero-filled locally). Files are the record; the state
store only indexes them.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class RunInfo(BaseModel):
    run_id: str
    started_at: str
    finished_at: str
    status: str


class JobInfo(BaseModel):
    namespace: str
    name: str


class QualityResult(BaseModel):
    structure: str
    column: str = ""
    rule: str
    passed: bool
    violations: int = 0


class Receipt(BaseModel):
    schema_version: int = 1
    run: RunInfo
    job: JobInfo
    facets: dict[str, str] = Field(default_factory=dict)
    layers: dict[str, dict[str, int]] = Field(default_factory=dict)
    quality: list[QualityResult] = Field(default_factory=list)
    cost: dict[str, float] = Field(default_factory=dict)


def write_receipt(receipt: Receipt, receipts_dir: Path | str) -> Path:
    """Write one receipt JSON file named <run_id>.json; return its path."""
    directory = Path(receipts_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (receipt.run.run_id + ".json")
    path.write_text(json.dumps(receipt.model_dump(), indent=2))
    return path
