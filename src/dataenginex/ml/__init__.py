"""Classical ML — training, registry, drift, serving, metrics.

LLM / vectorstore / scheduling live in ``dataenginex.ai`` and
``dataenginex.orchestration`` respectively.

Public API::

    from dataenginex.ml import (
        BaseTrainer, PyTorchTrainer, SklearnTrainer, TrainingResult,
        ModelRegistry, ModelArtifact, ModelStage, VERSION_AUTO,
        MLflowModelRegistry, MLflowRegistryError,
        DriftDetector, DriftReport,
        ModelServer, PredictionRequest, PredictionResponse,
        model_prediction_total, model_prediction_latency_seconds,
        model_drift_psi, model_drift_alerts_total,
    )
"""

from __future__ import annotations

from .drift import DriftDetector, DriftReport
from .metrics import (
    model_drift_alerts_total,
    model_drift_psi,
    model_prediction_latency_seconds,
    model_prediction_total,
)
from .mlflow_registry import MLflowModelRegistry, MLflowRegistryError
from .registry import VERSION_AUTO, ModelArtifact, ModelRegistry, ModelStage
from .serving import ModelServer, PredictionRequest, PredictionResponse
from .training import BaseTrainer, PyTorchTrainer, SklearnTrainer, TrainingResult

__all__ = [
    # Training
    "BaseTrainer",
    "PyTorchTrainer",
    "SklearnTrainer",
    "TrainingResult",
    # Registry
    "ModelArtifact",
    "ModelRegistry",
    "ModelStage",
    "VERSION_AUTO",
    "MLflowModelRegistry",
    "MLflowRegistryError",
    # Drift
    "DriftDetector",
    "DriftReport",
    # Serving
    "ModelServer",
    "PredictionRequest",
    "PredictionResponse",
    # Metrics
    "model_drift_alerts_total",
    "model_drift_psi",
    "model_prediction_latency_seconds",
    "model_prediction_total",
]
