"""Tests for dataenginex.ai.observability.langfuse sink."""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

from dataenginex.ai.llm import LLMResponse
from dataenginex.ai.observability.langfuse import (
    LangfuseSink,
    trace_generation,
)


def _response(text: str = "ok") -> LLMResponse:
    return LLMResponse(
        text=text,
        model="mock-model",
        prompt_tokens=4,
        completion_tokens=2,
        total_tokens=6,
    )


class TestLangfuseSinkDisabled:
    def test_no_client_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEX_LANGFUSE_ENABLED", "false")
        sink = LangfuseSink()
        assert sink.enabled is False
        sink.trace_generation(
            name="x",
            model="m",
            input_messages="hi",
            response=_response(),
        )  # no-op, no exception

    def test_no_op_flush(self) -> None:
        sink = LangfuseSink(enabled=False)
        sink.flush()

    def test_falls_back_when_langfuse_missing(self) -> None:
        original = sys.modules.get("langfuse")
        sys.modules["langfuse"] = None  # type: ignore[assignment]
        try:
            sink = LangfuseSink(enabled=True)
            assert sink.enabled is False
        finally:
            if original is not None:
                sys.modules["langfuse"] = original
            else:
                sys.modules.pop("langfuse", None)


class TestLangfuseSinkEnabled:
    def _install_fake_module(self) -> tuple[types.ModuleType, MagicMock]:
        fake = types.ModuleType("langfuse")
        client_instance = MagicMock()
        client_cls = MagicMock(return_value=client_instance)
        fake.Langfuse = client_cls  # type: ignore[attr-defined]
        sys.modules["langfuse"] = fake
        return fake, client_instance

    def teardown_method(self) -> None:
        sys.modules.pop("langfuse", None)

    def test_trace_generation_emits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEX_LANGFUSE_ENABLED", "true")
        _, client = self._install_fake_module()
        gen_ctx = MagicMock()
        client.start_as_current_generation.return_value.__enter__.return_value = gen_ctx

        sink = LangfuseSink()
        assert sink.enabled is True
        sink.trace_generation(
            name="summarise",
            model="gpt-4o",
            input_messages=[{"role": "user", "content": "x"}],
            response=_response("summary"),
            metadata={"agent": "builtin"},
            user_id="u1",
        )
        client.start_as_current_generation.assert_called_once()
        gen_ctx.update.assert_called_once()
        update_kwargs: dict[str, Any] = gen_ctx.update.call_args.kwargs
        assert update_kwargs["output"] == "summary"
        assert update_kwargs["usage_details"]["total"] == 6

    def test_trace_swallows_exceptions(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEX_LANGFUSE_ENABLED", "true")
        _, client = self._install_fake_module()
        client.start_as_current_generation.side_effect = RuntimeError("boom")

        sink = LangfuseSink()
        sink.trace_generation(
            name="x",
            model="m",
            input_messages="hi",
            response=_response(),
        )  # must not raise


class TestTraceGenerationContext:
    def test_disabled_sink_is_no_op(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEX_LANGFUSE_ENABLED", "false")
        import dataenginex.ai.observability.langfuse as mod

        mod._GLOBAL_SINK = None
        with trace_generation("task", model="mock") as ctx:
            ctx["input"] = "prompt"
            ctx["response"] = _response()
        # No exception; sink global remains disabled
        assert mod.get_sink().enabled is False
