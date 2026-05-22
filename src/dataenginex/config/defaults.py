"""Built-in default values for all config sections.

These are applied when a section is omitted from dex.yaml.
"""

from __future__ import annotations

# Data
DEFAULT_ENGINE = "duckdb"

# ML
DEFAULT_TRACKER = "builtin"
DEFAULT_FEATURE_STORE = "builtin"
DEFAULT_SERVING_ENGINE = "builtin"
DEFAULT_DRIFT_METHOD = "psi"
DEFAULT_DRIFT_THRESHOLD = 0.2

# AI
DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_LLM_MODEL = "qwen3:8b"
DEFAULT_RETRIEVAL_STRATEGY = "hybrid"
DEFAULT_VECTORSTORE_BACKEND = "builtin"
DEFAULT_AGENT_RUNTIME = "builtin"

# Observability
DEFAULT_LOG_LEVEL = "INFO"
