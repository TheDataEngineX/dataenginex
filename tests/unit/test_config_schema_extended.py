"""Tests for dataenginex.config.schema — all Pydantic config models."""

from __future__ import annotations

import pytest

from dataenginex.config.schema import (
    AgentConfig,
    AiConfig,
    AuditConfig,
    CollectionConfig,
    DataConfig,
    DexConfig,
    DriftConfig,
    ExperimentConfig,
    GuardConfig,
    LLMConfig,
    MlConfig,
    ObservabilityConfig,
    PiiConfig,
    PipelineConfig,
    ProjectConfig,
    QualityCheckConfig,
    RetrievalConfig,
    SecopsConfig,
    SourceConfig,
    TrackerConfig,
    TransformStepConfig,
    VectorStoreConfig,
)


class TestProjectConfig:
    def test_minimal(self) -> None:
        c = ProjectConfig(name="my-project")
        assert c.name == "my-project"
        assert c.version == "0.1.0"
        assert c.description == ""

    def test_full(self) -> None:
        c = ProjectConfig(name="test", version="2.0.0", description="A project")
        assert c.version == "2.0.0"

    def test_name_required(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProjectConfig()  # type: ignore[call-arg]


class TestSourceConfig:
    def test_minimal(self) -> None:
        s = SourceConfig(type="csv")
        assert s.type == "csv"
        assert s.path is None

    def test_with_path(self) -> None:
        s = SourceConfig(type="csv", path="/data/file.csv")
        assert s.path == "/data/file.csv"

    def test_all_fields(self) -> None:
        s = SourceConfig(
            type="postgres",
            path=None,
            query="SELECT * FROM table",
            url="postgresql://user:pass@host/db",
            connection={"sslmode": "require"},
            options={"timeout": 30},
        )
        assert s.type == "postgres"
        assert s.query == "SELECT * FROM table"


class TestTransformStepConfig:
    def test_filter_transform(self) -> None:
        t = TransformStepConfig(type="filter", condition="age > 18")
        assert t.type == "filter"
        assert t.condition == "age > 18"

    def test_sql_transform(self) -> None:
        t = TransformStepConfig(type="sql", sql="SELECT * FROM _data LIMIT 10")
        assert t.sql == "SELECT * FROM _data LIMIT 10"

    def test_cast_transform(self) -> None:
        t = TransformStepConfig(type="cast", columns={"age": "int"})
        assert t.columns == {"age": "int"}

    def test_derive_transform(self) -> None:
        t = TransformStepConfig(type="derive", name="full_name", expression="first + ' ' + last")
        assert t.name == "full_name"

    def test_deduplicate_transform(self) -> None:
        t = TransformStepConfig(type="deduplicate", key=["id", "email"])
        assert t.key == ["id", "email"]


class TestQualityCheckConfig:
    def test_defaults(self) -> None:
        q = QualityCheckConfig()
        assert q.completeness is None
        assert q.uniqueness is None

    def test_with_values(self) -> None:
        q = QualityCheckConfig(completeness=0.95, uniqueness=["id", "email"])
        assert q.completeness is not None and q.completeness > 0.9
        assert q.uniqueness is not None and "id" in q.uniqueness


class TestPipelineConfig:
    def test_minimal(self) -> None:
        p = PipelineConfig(source="raw_data")
        assert p.source == "raw_data"
        assert p.transforms == []
        assert p.schedule is None

    def test_with_schedule(self) -> None:
        p = PipelineConfig(source="data", schedule="0 * * * *")
        assert p.schedule == "0 * * * *"

    def test_with_transforms(self) -> None:
        t = TransformStepConfig(type="filter", condition="x > 0")
        p = PipelineConfig(source="data", transforms=[t])
        assert len(p.transforms) == 1

    def test_with_depends_on(self) -> None:
        p = PipelineConfig(source="data", depends_on=["bronze_pipeline"])
        assert "bronze_pipeline" in p.depends_on


class TestDataConfig:
    def test_defaults(self) -> None:
        d = DataConfig()
        assert d.engine == "duckdb"
        assert d.sources == {}
        assert d.pipelines == {}

    def test_with_sources(self) -> None:
        d = DataConfig(sources={"raw": SourceConfig(type="csv", path="data.csv")})
        assert "raw" in d.sources


class TestTrackerConfig:
    def test_defaults(self) -> None:
        t = TrackerConfig()
        assert t.backend is not None

    def test_custom_backend(self) -> None:
        t = TrackerConfig(backend="mlflow")
        assert t.backend == "mlflow"


class TestExperimentConfig:
    def test_minimal(self) -> None:
        e = ExperimentConfig(target="label")
        assert e.target == "label"
        assert e.features == []

    def test_with_features(self) -> None:
        e = ExperimentConfig(
            target="churn", features=["age", "spend"], params={"n_estimators": 100}
        )
        assert "age" in e.features
        assert e.params["n_estimators"] == 100


class TestDriftConfig:
    def test_defaults(self) -> None:
        d = DriftConfig()
        assert d.monitor == []

    def test_with_columns(self) -> None:
        d = DriftConfig(monitor=["spend", "age"])
        assert len(d.monitor) == 2


class TestMlConfig:
    def test_defaults(self) -> None:
        m = MlConfig()
        assert m.experiments == {}

    def test_with_experiment(self) -> None:
        m = MlConfig(experiments={"churn": ExperimentConfig(target="churned")})
        assert "churn" in m.experiments


class TestLLMConfig:
    def test_defaults(self) -> None:
        c = LLMConfig()
        assert c.provider is not None
        assert c.model is not None

    def test_custom(self) -> None:
        c = LLMConfig(provider="openai", model="gpt-4o")
        assert c.provider == "openai"
        assert c.model == "gpt-4o"


class TestRetrievalConfig:
    def test_defaults(self) -> None:
        r = RetrievalConfig()
        assert r.top_k > 0

    def test_custom(self) -> None:
        r = RetrievalConfig(strategy="bm25", top_k=10)
        assert r.strategy == "bm25"


class TestVectorStoreConfig:
    def test_defaults(self) -> None:
        v = VectorStoreConfig()
        assert v.backend is not None


class TestCollectionConfig:
    def test_defaults(self) -> None:
        c = CollectionConfig()
        assert c.chunk_size > 0


class TestAgentConfig:
    def test_minimal(self) -> None:
        a = AgentConfig(system_prompt="You are helpful.")
        assert a.system_prompt == "You are helpful."
        assert a.runtime == "builtin"
        assert a.tools == []

    def test_with_tools(self) -> None:
        a = AgentConfig(system_prompt="s", tools=["query", "pipeline_status"])
        assert "query" in a.tools


class TestAiConfig:
    def test_defaults(self) -> None:
        a = AiConfig()
        assert a.agents == {}

    def test_with_agent(self) -> None:
        a = AiConfig(agents={"assistant": AgentConfig(system_prompt="Hello")})
        assert "assistant" in a.agents


class TestPiiConfig:
    def test_defaults(self) -> None:
        p = PiiConfig()
        assert p.scan is not None


class TestAuditConfig:
    def test_defaults(self) -> None:
        a = AuditConfig()
        assert a.enabled is not None


class TestGuardConfig:
    def test_defaults(self) -> None:
        g = GuardConfig()
        assert g.enabled is not None


class TestSecopsConfig:
    def test_defaults(self) -> None:
        s = SecopsConfig()
        assert s.pii is not None
        assert s.audit is not None
        assert s.guard is not None


class TestObservabilityConfig:
    def test_defaults(self) -> None:
        o = ObservabilityConfig()
        assert o.metrics is not None


class TestDexConfig:
    def test_minimal(self) -> None:
        c = DexConfig(project=ProjectConfig(name="test"))
        assert c.project.name == "test"
        assert c.data is not None
        assert c.ml is not None
        assert c.ai is not None
        assert c.secops is not None

    def test_project_required(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DexConfig()  # type: ignore[call-arg]

    def test_full_config(self) -> None:
        c = DexConfig(
            project=ProjectConfig(name="full", version="1.0.0"),
            data=DataConfig(sources={"src": SourceConfig(type="csv")}),
            ml=MlConfig(),
            ai=AiConfig(),
            secops=SecopsConfig(),
            observability=ObservabilityConfig(),
        )
        assert c.project.name == "full"
        assert "src" in c.data.sources
