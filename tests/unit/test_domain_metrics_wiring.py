"""Tests verifying domain metrics are emitted from production code paths."""

from __future__ import annotations

from prometheus_client import REGISTRY

from dataenginex.ai.agents.builtin import BuiltinAgentRuntime
from dataenginex.ai.tools import ToolRegistry, ToolSpec
from dataenginex.ml.drift import DriftDetector  # noqa: F401 — ensures registration
from dataenginex.orchestration.scheduler import DriftMonitorConfig, DriftScheduler


def _sample_value(metric: str, labels: dict[str, str]) -> float:
    """Return the current value for a labeled sample from REGISTRY."""
    for family in REGISTRY.collect():
        for sample in family.samples:
            if sample.name == metric and sample.labels == labels:
                return float(sample.value)
    return 0.0


class TestAgentRuntimeMetrics:
    async def _run(self, agent: BuiltinAgentRuntime, message: str) -> None:
        await agent.run(message)

    def test_agent_iterations_observed_on_run(self) -> None:
        import asyncio

        agent = BuiltinAgentRuntime(llm=None, name="wiring-test")
        asyncio.run(agent.run("hello"))
        # Histogram bucket count: _count sample must exist for this agent
        observed = _sample_value("dex_ai_agent_iterations_count", {"agent": "wiring-test"})
        assert observed >= 1

    def test_tool_call_ok_counter_increments(self) -> None:
        import asyncio

        registry = ToolRegistry()
        registry.register(
            ToolSpec(
                name="echo",
                description="echo",
                fn=lambda text: text,
                parameters={"text": {"type": "string"}},
            )
        )

        class _ToolOnceLLM:
            def __init__(self) -> None:
                self._count = 0

            def chat(self, messages):  # type: ignore[no-untyped-def]
                from dataenginex.ai.llm import LLMResponse

                self._count += 1
                if self._count == 1:
                    return LLMResponse(text='TOOL: echo ARGS: {"text": "hi"}', model="m")
                return LLMResponse(text="ANSWER: done", model="m")

        before = _sample_value("dex_ai_tool_calls_total", {"tool": "echo", "status": "ok"})
        agent = BuiltinAgentRuntime(
            llm=_ToolOnceLLM(), tools=registry, name="tool-test", max_iterations=3
        )
        asyncio.run(agent.run("go"))
        after = _sample_value("dex_ai_tool_calls_total", {"tool": "echo", "status": "ok"})
        assert after >= before + 1


class TestDriftSchedulerEmitsDexGauge:
    def test_execute_check_sets_dex_drift_score(self) -> None:
        scheduler = DriftScheduler()
        config = DriftMonitorConfig(
            model_name="wiretest-model",
            reference_data={"feat_a": [0.0] * 50},
            check_interval_seconds=1.0,
        )
        scheduler.register(config, data_fn=lambda: {"feat_a": [1.0] * 50})
        scheduler.run_check("wiretest-model")

        value = _sample_value(
            "dex_ml_drift_score",
            {"pipeline": "wiretest-model", "feature": "feat_a", "method": "psi"},
        )
        # Equal-width binning on constant-reference data collapses to zero PSI,
        # but the gauge must have been published at all (sample exists).
        assert value >= 0.0
        # Proof of publish: sample must be present
        found = False
        for family in REGISTRY.collect():
            if family.name == "dex_ml_drift_score":
                for sample in family.samples:
                    if sample.labels.get("pipeline") == "wiretest-model":
                        found = True
                        break
        assert found, "dex_ml_drift_score was not published by the scheduler"


