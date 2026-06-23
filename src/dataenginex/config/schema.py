"""Pydantic models for dex.yaml — the unified config schema.

Every section is a Pydantic BaseModel with defaults so that
only ``project.name`` is required. Progressive disclosure:
add sections as you need them.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from dataenginex.config.defaults import (
    DEFAULT_AGENT_RUNTIME,
    DEFAULT_DRIFT_METHOD,
    DEFAULT_DRIFT_THRESHOLD,
    DEFAULT_ENGINE,
    DEFAULT_FEATURE_STORE,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LOG_LEVEL,
    DEFAULT_RETRIEVAL_STRATEGY,
    DEFAULT_SERVING_ENGINE,
    DEFAULT_TRACKER,
    DEFAULT_VECTORSTORE_BACKEND,
)

# --- Project ---


class ProjectConfig(BaseModel):
    """Top-level project metadata."""

    name: str
    version: str = "0.1.0"
    description: str = ""


# --- Data Layer ---


class SourceConfig(BaseModel):
    """A named data source."""

    type: str  # csv, duckdb, postgres, s3, rest, kafka, etc.
    path: str | None = None
    query: str | None = None
    url: str | None = None
    connection: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)


class TransformStepConfig(BaseModel):
    """A single transform step in a pipeline."""

    type: str  # filter, derive, cast, deduplicate, sql, rename, drop_columns, fill_null, aggregate
    condition: str | None = None  # filter
    expression: str | None = None  # derive, window
    name: str | None = None  # derive, window: output column name
    columns: dict[str, str] | list[str] | None = None  # cast: {col: type}, drop_columns: [col, ...]
    key: str | list[str] | None = None  # deduplicate
    sql: str | None = None  # sql
    mapping: dict[str, str] | None = None  # rename: {old_name: new_name}
    defaults: dict[str, Any] | None = None  # fill_null: {col: default_value}
    group_by: list[str] | None = None  # aggregate
    agg_exprs: dict[str, str] | None = None  # aggregate: {output_col: "expression"}
    partition_by: list[str] | None = None  # window
    order_by: str | None = None  # window
    options: dict[str, Any] = Field(default_factory=dict)


class QualityCheckConfig(BaseModel):
    """Quality checks applied after transforms."""

    completeness: float | None = None  # min non-null ratio (0.0-1.0)
    uniqueness: list[str] | None = None  # columns that must be unique
    row_count_min: int | None = None  # minimum number of rows required
    freshness_hours: float | None = None
    custom_sql: str | None = None


class PipelineConfig(BaseModel):
    """A named data pipeline."""

    source: str  # reference to a named source
    transforms: list[TransformStepConfig] = Field(default_factory=list)
    quality: QualityCheckConfig | None = None
    destination: str | None = None
    target: dict[str, str] | None = None  # {layer: "silver"}
    depends_on: list[str] = Field(default_factory=list)
    schedule: str | None = None  # cron expression


class DataConfig(BaseModel):
    """Data layer configuration."""

    engine: str = DEFAULT_ENGINE
    sources: dict[str, SourceConfig] = Field(default_factory=dict)
    pipelines: dict[str, PipelineConfig] = Field(default_factory=dict)


# --- ML Layer ---


class TrackerConfig(BaseModel):
    """Experiment tracker backend config."""

    backend: str = DEFAULT_TRACKER
    uri: str | None = None  # for mlflow


class FeatureStoreConfig(BaseModel):
    """Feature store backend config."""

    backend: str = DEFAULT_FEATURE_STORE
    options: dict[str, Any] = Field(default_factory=dict)


class DriftConfig(BaseModel):
    """Drift detection configuration."""

    monitor: list[str] = Field(default_factory=list)
    method: str = DEFAULT_DRIFT_METHOD
    threshold: float = DEFAULT_DRIFT_THRESHOLD


class ServingConfig(BaseModel):
    """Model serving config."""

    engine: str = DEFAULT_SERVING_ENGINE
    endpoints: list[dict[str, Any]] = Field(default_factory=list)


class ExperimentConfig(BaseModel):
    """An ML experiment definition."""

    model_type: str = "sklearn"
    target: str = ""
    features: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)


class MlConfig(BaseModel):
    """ML layer configuration."""

    tracker: str = DEFAULT_TRACKER
    tracking: TrackerConfig = Field(default_factory=TrackerConfig)
    features: FeatureStoreConfig = Field(default_factory=FeatureStoreConfig)
    experiments: dict[str, ExperimentConfig] = Field(default_factory=dict)
    serving: ServingConfig = Field(default_factory=ServingConfig)
    drift: DriftConfig = Field(default_factory=DriftConfig)


# --- AI Layer ---


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = DEFAULT_LLM_PROVIDER
    model: str = DEFAULT_LLM_MODEL
    fallback: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class RetrievalConfig(BaseModel):
    """Retrieval strategy configuration."""

    strategy: str = DEFAULT_RETRIEVAL_STRATEGY
    top_k: int = 10
    reranker: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class VectorStoreConfig(BaseModel):
    """Vector store backend configuration."""

    backend: str = DEFAULT_VECTORSTORE_BACKEND
    embedding_model: str = "all-MiniLM-L6-v2"
    options: dict[str, Any] = Field(default_factory=dict)


class CollectionConfig(BaseModel):
    """A named vector collection."""

    source: str | None = None  # pipeline that populates it
    embedding_model: str | None = None  # override default
    chunk_size: int = 512
    chunk_overlap: int = 50


class AgentConfig(BaseModel):
    """An AI agent definition."""

    runtime: str = DEFAULT_AGENT_RUNTIME
    system_prompt: str = ""
    tools: list[str] = Field(default_factory=list)
    model: str | None = None  # override default LLM
    max_iterations: int = 10
    memory: Literal["short_term", "episodic", "long_term"] = "short_term"


class AiConfig(BaseModel):
    """AI layer configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    vectorstore: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    collections: dict[str, CollectionConfig] = Field(default_factory=dict)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)


# --- SecOps ---


class PiiConfig(BaseModel):
    """PII detection configuration."""

    scan: bool = False
    patterns: list[str] = Field(default_factory=lambda: ["email", "ssn", "phone", "credit_card"])
    action: Literal["warn", "mask", "block"] = "warn"


class AuditConfig(BaseModel):
    """Audit logging configuration.

    Attributes:
        enabled: Master switch. When ``True`` a :class:`~dataenginex.secops.AuditLogger`
            is created and attached to the :class:`~dataenginex.secops.PrivacyGuard`
            so every PII detection/masking event is persisted.
        db_path: DuckDB database path for the audit log.  Leave empty (default)
            for in-memory-only logging (data lost on restart). Set to a relative
            path (e.g. ``"secops_audit.db"``) and it is resolved under the
            project's ``.dex/`` directory; use an absolute path for a custom
            location.
    """

    enabled: bool = False
    db_path: str = ""  # empty → :memory: (no persistence)


class GuardConfig(BaseModel):
    """Outbound LLM call guard (``PrivacyGuard``) configuration.

    Wraps every external LLM provider call with PII detection and either
    masking or blocking. Local providers (Ollama, etc.) bypass guarding
    by default since their data never leaves the machine.

    Attributes:
        enabled: Master switch. When ``False`` the guard logs once and
            passes all prompts through unchanged.
        allow_local: When ``True``, prompts to local providers bypass
            scanning. Disable to scan local calls too (e.g. for audit-only).
        block_on_detect: When ``True``, prompts containing PII raise
            ``PrivacyBlocked`` instead of being masked.
        log_all_outbound: Emit a structlog entry for every outbound call.
        strategies: Map of PII type → masking strategy, e.g.
            ``{"email": "hash", "ssn": "redact"}``. PII types absent from
            this map fall back to the masker's default (``REDACT``).
        local_targets: Provider names treated as local (bypass scan).
    """

    enabled: bool = True
    allow_local: bool = True
    block_on_detect: bool = False
    log_all_outbound: bool = True
    strategies: dict[str, str] = Field(default_factory=dict)
    local_targets: list[str] = Field(default_factory=lambda: ["ollama", "local"])


class SecopsConfig(BaseModel):
    """Security operations configuration."""

    pii: PiiConfig = Field(default_factory=PiiConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    guard: GuardConfig = Field(default_factory=GuardConfig)


# --- Observability ---


class ObservabilityConfig(BaseModel):
    """Observability configuration."""

    metrics: bool = True
    tracing: bool = False
    log_level: str = DEFAULT_LOG_LEVEL


# --- Root Config ---


class DexConfig(BaseModel):
    """Root configuration model — one ``dex.yaml`` defines everything.

    Only ``project`` is required. All other sections have sensible defaults.
    """

    project: ProjectConfig
    data: DataConfig = Field(default_factory=DataConfig)
    ml: MlConfig = Field(default_factory=MlConfig)
    ai: AiConfig = Field(default_factory=AiConfig)
    secops: SecopsConfig = Field(default_factory=SecopsConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
