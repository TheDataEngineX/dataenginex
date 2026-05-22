"""Middleware — logging, metrics, and domain-level Prometheus counters.

Public API::

    from dataenginex.middleware import configure_logging, get_logger
    from dataenginex.middleware import get_metrics
    from dataenginex.middleware.domain_metrics import pipeline_runs_total, ai_tokens_total
"""

from __future__ import annotations

from dataenginex.middleware.domain_metrics import (
    ai_agent_iterations,
    ai_tokens_total,
    ai_tool_calls_total,
    ml_drift_score,
    ml_model_predictions_total,
    pipeline_run_duration_seconds,
    pipeline_runs_total,
    quality_gate_evaluations_total,
    tenant_operations_total,
)
from dataenginex.middleware.logging_config import APP_VERSION, configure_logging, get_logger
from dataenginex.middleware.metrics import get_metrics

__all__ = [
    # Logging
    "APP_VERSION",
    "configure_logging",
    "get_logger",
    # Metrics
    "get_metrics",
    # Domain metrics
    "ai_agent_iterations",
    "ai_tokens_total",
    "ai_tool_calls_total",
    "ml_drift_score",
    "ml_model_predictions_total",
    "pipeline_run_duration_seconds",
    "pipeline_runs_total",
    "quality_gate_evaluations_total",
    "tenant_operations_total",
]
