"""Connector registry and public API."""

from __future__ import annotations

from dataenginex.core.interfaces import BaseConnector
from dataenginex.core.registry import BackendRegistry

connector_registry: BackendRegistry[BaseConnector] = BackendRegistry("connector")

from dataenginex.data.connectors.csv import CsvConnector  # noqa: E402, F401
from dataenginex.data.connectors.dbt import DbtConnector  # noqa: E402, F401
from dataenginex.data.connectors.delta import DeltaConnector  # noqa: E402, F401
from dataenginex.data.connectors.duckdb import DuckDBConnector  # noqa: E402, F401
from dataenginex.data.connectors.http import HttpConnector  # noqa: E402, F401
from dataenginex.data.connectors.kafka import KafkaConnector  # noqa: E402, F401
from dataenginex.data.connectors.parquet import ParquetConnector  # noqa: E402, F401
from dataenginex.data.connectors.rest import RestApiConnector  # noqa: E402, F401
from dataenginex.data.connectors.spark import SparkConnector  # noqa: E402, F401
from dataenginex.data.connectors.sse import SseConnector  # noqa: E402, F401

__all__ = [
    "BaseConnector",
    "connector_registry",
    "CsvConnector",
    "DbtConnector",
    "DeltaConnector",
    "DuckDBConnector",
    "HttpConnector",
    "KafkaConnector",
    "ParquetConnector",
    "RestApiConnector",
    "SparkConnector",
    "SseConnector",
]
