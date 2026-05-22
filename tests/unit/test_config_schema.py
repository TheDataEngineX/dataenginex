"""Tests for dex.yaml Pydantic schema models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from dataenginex.config.schema import (
    AiConfig,
    DataConfig,
    DexConfig,
    MlConfig,
    PipelineConfig,
    ProjectConfig,
    SourceConfig,
)


class TestProjectConfig:
    def test_minimal(self) -> None:
        cfg = ProjectConfig(name="test-project")
        assert cfg.name == "test-project"
        assert cfg.version == "0.1.0"

    def test_with_version(self) -> None:
        cfg = ProjectConfig(name="demo", version="1.0.0")
        assert cfg.version == "1.0.0"


class TestSourceConfig:
    def test_csv_source(self) -> None:
        cfg = SourceConfig(type="csv", path="data/input.csv")
        assert cfg.type == "csv"

    def test_duckdb_source(self) -> None:
        cfg = SourceConfig(type="duckdb", query="SELECT * FROM users")
        assert cfg.type == "duckdb"


class TestPipelineConfig:
    def test_minimal_pipeline(self) -> None:
        cfg = PipelineConfig(
            source="raw_data",
            transforms=[],
            destination="silver_users",
        )
        assert cfg.source == "raw_data"
        assert len(cfg.transforms) == 0


class TestDataConfig:
    def test_with_sources_and_pipelines(self) -> None:
        cfg = DataConfig(
            sources={
                "users": SourceConfig(type="csv", path="data/users.csv"),
            },
            pipelines={
                "clean_users": PipelineConfig(
                    source="users",
                    transforms=[],
                    destination="silver_users",
                ),
            },
        )
        assert "users" in cfg.sources
        assert "clean_users" in cfg.pipelines

    def test_default_engine_is_duckdb(self) -> None:
        cfg = DataConfig()
        assert cfg.engine == "duckdb"


class TestMlConfig:
    def test_defaults(self) -> None:
        cfg = MlConfig()
        assert cfg.tracker == "builtin"


class TestAiConfig:
    def test_defaults(self) -> None:
        cfg = AiConfig()
        assert cfg.llm.provider == "ollama"


class TestDexConfig:
    def test_minimal_valid_config(self) -> None:
        cfg = DexConfig(project=ProjectConfig(name="minimal"))
        assert cfg.project.name == "minimal"
        assert cfg.data.engine == "duckdb"
        assert cfg.ml.tracker == "builtin"

    def test_all_sections_optional_except_project(self) -> None:
        with pytest.raises(ValidationError):
            DexConfig()  # type: ignore[call-arg]

    def test_no_server_field(self) -> None:
        cfg = DexConfig(project=ProjectConfig(name="srv"))
        assert not hasattr(cfg, "server")
