"""Connector registry and public API."""

from __future__ import annotations

from dataenginex.core.interfaces import BaseConnector
from dataenginex.core.registry import BackendRegistry

# New registry-based connector system
connector_registry: BackendRegistry[BaseConnector] = BackendRegistry("connector")

# Auto-register built-in connector backends
from dataenginex.data.connectors.csv import CsvConnector  # noqa: F401
from dataenginex.data.connectors.duckdb import DuckDBConnector  # noqa: F401
from dataenginex.data.connectors.parquet import ParquetConnector  # noqa: F401

# Re-export legacy connector classes for backward compatibility
from dataenginex.data.connectors.legacy import (  # noqa: E402
    ConnectorStatus,
    DataConnector,
    FetchResult,
    FileConnector,
    RestConnector,
)

__all__ = [
    # New
    "BaseConnector",
    "connector_registry",
    # Legacy
    "ConnectorStatus",
    "DataConnector",
    "FetchResult",
    "FileConnector",
    "RestConnector",
]
