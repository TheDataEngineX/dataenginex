"""Orchestration — scheduling and execution coordination."""

from __future__ import annotations

from dataenginex.core.interfaces import BaseOrchestrator
from dataenginex.core.registry import BackendRegistry
from dataenginex.orchestration.scheduler import (
    DataProvider,
    DriftCheckResult,
    DriftMonitorConfig,
    DriftScheduler,
)

orchestrator_registry: BackendRegistry[BaseOrchestrator] = BackendRegistry("orchestrator")

__all__ = [
    "BaseOrchestrator",
    "orchestrator_registry",
    "DataProvider",
    "DriftCheckResult",
    "DriftMonitorConfig",
    "DriftScheduler",
]
