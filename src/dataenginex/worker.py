"""ARQ async job worker for DataEngineX.

Run with::

    arq dataenginex.worker.WorkerSettings

Environment variables:
    DEX_REDIS_URL   Redis DSN (default: redis://localhost:6379)
    DEX_CONFIG_PATH Path to dex.yaml (default: dex.yaml)

Jobs:
    run_pipeline(pipeline_name)   Execute a named pipeline from dex.yaml
    train_model(experiment_name)  Train an ML model from dex.yaml
    run_agent(agent_name, message) Run a one-shot agent task
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import structlog
from arq.connections import RedisSettings

logger = structlog.get_logger()

_REDIS_URL = os.getenv("DEX_REDIS_URL", "redis://localhost:6379")
_CONFIG_PATH = Path(os.getenv("DEX_CONFIG_PATH", "dex.yaml")).resolve()
_PROJECT_DIR = _CONFIG_PATH.parent
_DEX_DIR = _PROJECT_DIR / ".dex"


def _load_config() -> Any:
    from dataenginex.config.loader import load_config

    return load_config(_CONFIG_PATH)


async def run_pipeline(ctx: dict[str, Any], pipeline_name: str) -> dict[str, Any]:
    """Execute a pipeline run asynchronously.

    Args:
        ctx: ARQ context (contains redis pool).
        pipeline_name: Name of the pipeline in dex.yaml.

    Returns:
        Dict with success, rows_input, rows_output, steps_completed, error.
    """
    log = logger.bind(job="run_pipeline", pipeline=pipeline_name)
    log.info("pipeline.job.start")
    try:
        config = _load_config()
        from dataenginex.data.pipeline.runner import PipelineRunner
        from dataenginex.warehouse.lineage import PersistentLineage

        lineage = PersistentLineage(str(_DEX_DIR / "lineage.json"))
        runner = PipelineRunner(
            config,
            data_dir=_DEX_DIR / "lakehouse",
            project_dir=_PROJECT_DIR,
            lineage=lineage,
        )
        result = runner.run(pipeline_name)
        log.info("pipeline.job.done", success=result.success, rows=result.rows_output)
        return {
            "success": result.success,
            "rows_input": result.rows_input,
            "rows_output": result.rows_output,
            "steps_completed": result.steps_completed,
            "error": result.error,
        }
    except Exception as exc:
        log.error("pipeline.job.error", error=str(exc))
        return {
            "success": False,
            "rows_input": 0,
            "rows_output": 0,
            "steps_completed": 0,
            "error": str(exc),
        }


async def train_model(ctx: dict[str, Any], experiment_name: str) -> dict[str, Any]:
    """Train a model from the dex.yaml experiment config.

    Args:
        ctx: ARQ context.
        experiment_name: Name of experiment in dex.yaml ml.experiments.

    Returns:
        Dict with success, metrics, error.
    """
    log = logger.bind(job="train_model", experiment=experiment_name)
    log.info("train.job.start")
    try:
        config = _load_config()
        if experiment_name not in config.ml.experiments:
            return {
                "success": False,
                "metrics": {},
                "error": f"Experiment '{experiment_name}' not found",
            }
        from dataenginex.ml.training import train_experiment

        metrics = train_experiment(config, experiment_name, project_dir=_PROJECT_DIR)
        log.info("train.job.done", metrics=metrics)
        return {"success": True, "metrics": metrics, "error": None}
    except Exception as exc:
        log.error("train.job.error", error=str(exc))
        return {"success": False, "metrics": {}, "error": str(exc)}


async def run_agent(ctx: dict[str, Any], agent_name: str, message: str) -> dict[str, Any]:
    """Run a one-shot agent task asynchronously.

    Args:
        ctx: ARQ context.
        agent_name: Name of agent in dex.yaml ai.agents.
        message: User message to send to the agent.

    Returns:
        Dict with response, iterations, tool_calls, error.
    """
    log = logger.bind(job="run_agent", agent=agent_name)
    log.info("agent.job.start")
    try:
        config = _load_config()
        import dataenginex.ai.agents.builtin  # noqa: F401 — trigger registration
        from dataenginex.ai.agents import agent_registry
        from dataenginex.ai.llm import get_llm_provider
        from dataenginex.ai.tools import tool_registry
        from dataenginex.ai.tools.builtin import register_builtin_tools

        register_builtin_tools(
            lakehouse_dir=_DEX_DIR / "lakehouse",
            models_dir=_DEX_DIR / "models",
        )
        if agent_name not in config.ai.agents:
            return {
                "response": "",
                "iterations": 0,
                "tool_calls": [],
                "error": f"Agent '{agent_name}' not found",
            }

        cfg = config.ai.agents[agent_name]
        llm = get_llm_provider(config.ai.llm.provider, model=cfg.model or config.ai.llm.model)
        agent_cls: Any = cast(Any, agent_registry.get(cfg.runtime))
        agent = agent_cls(
            llm=llm,
            system_prompt=cfg.system_prompt,
            tools=tool_registry,
            max_iterations=cfg.max_iterations,
            timeout_seconds=cfg.timeout_seconds,
            name=agent_name,
        )
        result: dict[str, Any] = await agent.run(message)
        log.info("agent.job.done", iterations=result.get("iterations"))
        return {
            "response": result.get("response", ""),
            "iterations": result.get("iterations", 0),
            "tool_calls": result.get("tool_calls", []),
            "error": None,
        }
    except Exception as exc:
        log.error("agent.job.error", error=str(exc))
        return {"response": "", "iterations": 0, "tool_calls": [], "error": str(exc)}


class WorkerSettings:
    """ARQ worker settings.

    Usage::

        arq dataenginex.worker.WorkerSettings
    """

    functions = [run_pipeline, train_model, run_agent]
    redis_settings = RedisSettings.from_dsn(_REDIS_URL)
    max_jobs = 10
    job_timeout = 3600  # 1 hour max per job
    keep_result = 86400  # keep results for 24h
    retry_jobs = True
    max_tries = 3
