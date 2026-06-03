"""Tests for core/schemas.py (API response models) and core/exceptions.py."""

from __future__ import annotations

import pytest

from dataenginex.core.exceptions import (
    AgentError,
    BackendNotInstalledError,
    ConfigError,
    ConfigValidationError,
    DataEngineXError,
    LLMProviderError,
    PipelineError,
    PipelineStepError,
    RegistryError,
    ServingError,
    TrainingError,
)
from dataenginex.core.schemas import (
    ComponentStatus,
    EchoRequest,
    EchoResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    ReadinessResponse,
    RootResponse,
    StartupResponse,
)

# ── core/schemas.py ───────────────────────────────────────────────────────────


class TestRootResponse:
    def test_fields(self) -> None:
        r = RootResponse(message="hello", version="1.0.0")
        assert r.message == "hello"
        assert r.version == "1.0.0"

    def test_serialise(self) -> None:
        r = RootResponse(message="DataEngineX API", version="0.1.0")
        d = r.model_dump()
        assert d["message"] == "DataEngineX API"


class TestHealthResponse:
    def test_status_field(self) -> None:
        h = HealthResponse(status="alive")
        assert h.status == "alive"

    def test_json_round_trip(self) -> None:
        h = HealthResponse(status="ok")
        assert HealthResponse.model_validate_json(h.model_dump_json()).status == "ok"


class TestStartupResponse:
    def test_fields(self) -> None:
        s = StartupResponse(status="started")
        assert s.status == "started"


class TestComponentStatus:
    def test_minimal(self) -> None:
        c = ComponentStatus(name="db", status="healthy")
        assert c.name == "db"
        assert c.message is None
        assert c.duration_ms is None

    def test_with_all_fields(self) -> None:
        c = ComponentStatus(name="cache", status="degraded", message="slow", duration_ms=42.5)
        assert c.duration_ms == 42.5

    def test_serialise(self) -> None:
        c = ComponentStatus(name="x", status="ok")
        d = c.model_dump()
        assert "name" in d and "status" in d


class TestReadinessResponse:
    def test_fields(self) -> None:
        r = ReadinessResponse(status="ready", components=[])
        assert r.status == "ready"
        assert r.components == []

    def test_with_components(self) -> None:
        c = ComponentStatus(name="db", status="ok")
        r = ReadinessResponse(status="ready", components=[c])
        assert len(r.components) == 1


class TestErrorDetail:
    def test_fields(self) -> None:
        e = ErrorDetail(field="name", message="required")
        assert e.field == "name"
        assert e.message == "required"


class TestErrorResponse:
    def test_fields(self) -> None:
        e = ErrorResponse(error="not_found", message="Resource not found")
        assert e.error == "not_found"
        assert e.details is None

    def test_with_details(self) -> None:
        detail = ErrorDetail(field="id", message="invalid")
        e = ErrorResponse(error="bad_request", message="Validation error", details=[detail])
        assert len(e.details) == 1  # type: ignore[arg-type]

    def test_error_detail_optional_fields(self) -> None:
        d = ErrorDetail(message="required field missing")
        assert d.field is None
        assert d.type is None


class TestEchoModels:
    def test_echo_request(self) -> None:
        req = EchoRequest(message="ping")
        assert req.message == "ping"
        assert req.count == 1

    def test_echo_response(self) -> None:
        resp = EchoResponse(message="pong", count=2, echo=["pong", "pong"])
        assert resp.message == "pong"
        assert len(resp.echo) == 2


# ── core/exceptions.py ────────────────────────────────────────────────────────


class TestExceptionHierarchyExtended:
    def test_base_is_exception(self) -> None:
        e = DataEngineXError("test")
        assert isinstance(e, Exception)

    def test_config_error(self) -> None:
        e = ConfigError("bad config")
        assert isinstance(e, DataEngineXError)

    def test_config_validation_error_fields(self) -> None:
        e = ConfigValidationError("field.name", "must be a string")
        assert e.field == "field.name"
        assert e.message == "must be a string"
        assert "field.name" in str(e)
        assert isinstance(e, ConfigError)

    def test_pipeline_error(self) -> None:
        e = PipelineError("pipeline blew up")
        assert isinstance(e, DataEngineXError)

    def test_pipeline_step_error_full(self) -> None:
        e = PipelineStepError("transform", "null value", pipeline="ingest")
        assert e.step == "transform"
        assert e.pipeline == "ingest"
        assert "[ingest]" in str(e)
        assert isinstance(e, PipelineError)

    def test_pipeline_step_error_no_pipeline(self) -> None:
        e = PipelineStepError("load", "timeout")
        assert e.pipeline == ""
        assert "[" not in str(e)

    def test_pipeline_step_error_message_kwarg(self) -> None:
        e = PipelineStepError("step", message="via message kwarg")
        assert e.cause == "via message kwarg"

    def test_registry_error(self) -> None:
        e = RegistryError("unknown backend")
        assert isinstance(e, DataEngineXError)

    def test_backend_not_installed(self) -> None:
        e = BackendNotInstalledError("qdrant", "qdrant")
        assert e.backend == "qdrant"
        assert e.extra == "qdrant"
        assert "pip install" in str(e)

    def test_training_error(self) -> None:
        e = TrainingError("model failed")
        assert isinstance(e, DataEngineXError)

    def test_serving_error(self) -> None:
        e = ServingError("serving failed")
        assert isinstance(e, DataEngineXError)

    def test_agent_error(self) -> None:
        e = AgentError("agent crashed")
        assert isinstance(e, DataEngineXError)

    def test_llm_provider_error(self) -> None:
        e = LLMProviderError("openai", "rate limited")
        assert e.provider == "openai"
        assert "openai" in str(e)
        assert "rate limited" in str(e)
        assert isinstance(e, AgentError)

    def test_raise_and_catch_base(self) -> None:
        with pytest.raises(DataEngineXError):
            raise ConfigValidationError("x", "bad")

    def test_raise_and_catch_specific(self) -> None:
        with pytest.raises(ConfigValidationError):
            raise ConfigValidationError("x", "bad")
