"""Data layer — connectors, transforms, quality gates, pipelines.

Public API::

    from dataenginex.data import (
        # New registry-based API
        connector_registry, transform_registry,
        DuckDBConnector, CsvConnector,
        PipelineRunner, PipelineResult,
        QualityResult, check_quality,
        # Legacy API
        DataConnector, RestConnector, FileConnector,
        ConnectorStatus, FetchResult,
        DataProfiler, ProfileReport, ColumnProfile,
        SchemaRegistry, SchemaVersion,
    )
"""

from __future__ import annotations

# New Phase 1 API
from dataenginex.data.connectors import connector_registry
from dataenginex.data.connectors.csv import CsvConnector
from dataenginex.data.connectors.duckdb import DuckDBConnector

# Legacy API (backward-compatible)
from dataenginex.data.connectors.legacy import (
    ConnectorStatus,
    DataConnector,
    FetchResult,
    FileConnector,
    RestConnector,
)
from dataenginex.data.connectors.parquet import ParquetConnector
from dataenginex.data.pipeline.runner import PipelineResult, PipelineRunner
from dataenginex.data.profiler import ColumnProfile, DataProfiler, ProfileReport
from dataenginex.data.quality.gates import QualityResult, check_quality
from dataenginex.data.registry import SchemaRegistry, SchemaVersion
from dataenginex.data.transforms import transform_registry

__all__ = [
    # New
    "CsvConnector",
    "DuckDBConnector",
    "ParquetConnector",
    "PipelineResult",
    "PipelineRunner",
    "QualityResult",
    "check_quality",
    "connector_registry",
    "transform_registry",
    # Legacy
    "ColumnProfile",
    "ConnectorStatus",
    "DataConnector",
    "DataProfiler",
    "FetchResult",
    "FileConnector",
    "ProfileReport",
    "RestConnector",
    "SchemaRegistry",
    "SchemaVersion",
]
