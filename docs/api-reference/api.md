# dataenginex.api

HTTP helpers — error types, response models, and shared utilities.

`dataenginex` does **not** bundle a FastAPI server. This module provides the building blocks
for applications (like DEX Studio or your own FastAPI app) that want to expose DEX functionality
over HTTP.

## Error Types

```python
from dataenginex.api.errors import (
    NotFoundError,
    ValidationError,
    ConflictError,
    ServiceUnavailableError,
)
```

Standard Pydantic response models for HTTP error responses, usable in any FastAPI app:

```python
from fastapi import FastAPI
from dataenginex.api.errors import NotFoundError

app = FastAPI()

@app.get("/pipelines/{name}")
def get_pipeline(name: str):
    pipeline = engine.config.data.pipelines.get(name)
    if pipeline is None:
        raise NotFoundError(detail=f"Pipeline '{name}' not found")
    return pipeline
```

## Building an HTTP Layer

To expose DEX functionality over HTTP, create a FastAPI app in your application
and call `DexEngine` directly:

```python
from fastapi import FastAPI
from dataenginex.engine import DexEngine

engine = DexEngine("dex.yaml")
app = FastAPI()

@app.get("/health")
def health():
    return engine.health()

@app.get("/pipelines")
def list_pipelines():
    return list(engine.config.data.pipelines.keys())

@app.post("/pipelines/{name}/run")
def run_pipeline(name: str):
    return engine.run_pipeline(name)
```

See `examples/02_api_quickstart.py` for a minimal working example.

::: dataenginex.api
