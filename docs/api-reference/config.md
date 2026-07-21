# dataenginex.config

Config schema, loader, settings, and defaults. The `dex.yaml` file is parsed into a typed `DexConfig` object that drives the engine.

## Quick import

```python
from dataenginex.config import DexConfig, load_config, DexSettings
```

______________________________________________________________________

## Schema

`dataenginex.config.schema`

Pydantic models for `dex.yaml`. Covers pipelines, connectors, transforms, ML, AI, secops, and lakehouse config blocks.

::: dataenginex.config.schema

**Key model:** `DexConfig`

```python
from dataenginex.config.schema import DexConfig

config = DexConfig.model_validate({
    "pipelines": {
        "ingest_events": {
            "source": {"type": "csv", "path": "data/raw/events.csv"},
            "destination": {"type": "parquet", "path": "data/bronze/events"},
        }
    }
})
```

______________________________________________________________________

## Loader

`dataenginex.config.loader`

Loads and validates `dex.yaml` (or a custom path) with environment variable interpolation and secret resolution.

::: dataenginex.config.loader

**Key function:** `load_config`

```python
from dataenginex.config.loader import load_config

config = load_config("dex.yaml")
```

______________________________________________________________________

## Settings

`dataenginex.config.settings`

Runtime settings sourced from environment variables (`.env` or system env). Declares typed fields for well-known vars (e.g. `tmdb_api_key`); any other `.env`/env var is still picked up and exposed via `as_env_dict()` for `${VAR}` interpolation in `dex.yaml`.

::: dataenginex.config.settings

**Key class:** `DexSettings`

```python
from dataenginex.config.settings import DexSettings

settings = DexSettings()
print(settings.tmdb_api_key)          # "" unless TMDB_API_KEY is set
print(settings.get("SOME_ENV_VAR"))   # case-insensitive lookup across .env + os.environ
```

See `.env.template` in the project root for all available settings.

______________________________________________________________________

## Defaults

`dataenginex.config.defaults`

Default values applied when config keys are omitted.

::: dataenginex.config.defaults
