# dataenginex.ml

Classical ML — training, model registry, drift detection, and model serving.

LLM providers, vector stores, agents, and RAG live in `dataenginex.ai`.
The drift scheduler lives in `dataenginex.orchestration`.

## Module Split

| Concern | Module |
|---------|--------|
| Training, registry, serving, drift | `dataenginex.ml` |
| LLM providers, chat, embeddings | `dataenginex.ai.llm` |
| Vector stores | `dataenginex.ai.vectorstore` |
| Background drift scheduling | `dataenginex.orchestration.scheduler` |

## Quick Usage

```python
from dataenginex.ml import (
    SklearnTrainer, TrainingResult,
    ModelRegistry, ModelArtifact, ModelStage,
    DriftDetector, DriftReport,
    ModelServer, PredictionRequest, PredictionResponse,
)

# Train
trainer = SklearnTrainer(experiment_name="churn")
result: TrainingResult = trainer.train(X_train, y_train)

# Register
registry = ModelRegistry()
registry.register(result.model, name="churn_v1", stage=ModelStage.STAGING)

# Drift
detector = DriftDetector(reference=X_train)
report: DriftReport = detector.detect(X_new)

# Serve
server = ModelServer()
server.load("churn_v1", stage=ModelStage.PRODUCTION)
resp = server.predict(PredictionRequest(features={"age": 35}))
```

::: dataenginex.ml
