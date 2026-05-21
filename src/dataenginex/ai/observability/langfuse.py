"""Langfuse tracing sink — ship LLM traces to self-hosted or cloud Langfuse.

Records :class:`LLMResponse` calls as generation spans in Langfuse. Falls
back to a no-op when the ``langfuse`` optional dependency is missing or the
sink is disabled via env var.

Configuration (env vars)::

    DEX_LANGFUSE_ENABLED    — "true" to activate the sink (default "false")
    LANGFUSE_PUBLIC_KEY     — project public key
    LANGFUSE_SECRET_KEY     — project secret key
    LANGFUSE_HOST           — endpoint (default https://cloud.langfuse.com)

Install::

    uv sync --group observability

Example::

    from dataenginex.ai.observability.langfuse import trace_generation

    with trace_generation(name="summarise", model="gpt-4o") as ctx:
        ctx["input"] = prompt
        ctx["response"] = llm.generate(prompt)
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import structlog

from dataenginex.ai.llm import LLMResponse

logger = structlog.get_logger()

__all__ = ["LangfuseSink", "get_sink", "trace_generation"]


class LangfuseSink:
    """Thin wrapper over the Langfuse v4 SDK client.

    All public methods are safe to call unconditionally — when langfuse is
    not installed or the sink is disabled, they are no-ops.

    Args:
        public_key: Langfuse project public key; falls back to
            ``LANGFUSE_PUBLIC_KEY`` env var.
        secret_key: Langfuse project secret key; falls back to
            ``LANGFUSE_SECRET_KEY`` env var.
        host: Langfuse endpoint; falls back to ``LANGFUSE_HOST`` env var
            (default ``https://cloud.langfuse.com``).
        enabled: Override the ``DEX_LANGFUSE_ENABLED`` env var.
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self._enabled = self._resolve_enabled(enabled)
        self._client: Any = None
        if not self._enabled:
            return
        try:
            from langfuse import Langfuse
        except ImportError:
            logger.warning(
                "langfuse not installed — tracing disabled; "
                "install with: uv sync --group observability",
            )
            self._enabled = False
            return
        try:
            self._client = Langfuse(
                public_key=public_key or os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                secret_key=secret_key or os.getenv("LANGFUSE_SECRET_KEY", ""),
                host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
            logger.info(
                "langfuse sink initialised",
                host=host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            )
        except Exception as exc:  # noqa: BLE001 — langfuse init surface varies
            logger.warning("langfuse init failed", error=str(exc))
            self._enabled = False

    @staticmethod
    def _resolve_enabled(explicit: bool | None) -> bool:
        if explicit is not None:
            return explicit
        return os.getenv("DEX_LANGFUSE_ENABLED", "false").lower() == "true"

    @property
    def enabled(self) -> bool:
        """Whether the sink will emit traces on call."""
        return self._enabled and self._client is not None

    def trace_generation(
        self,
        *,
        name: str,
        model: str,
        input_messages: list[dict[str, str]] | str,
        response: LLMResponse,
        metadata: dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> None:
        """Record a single generation event in Langfuse."""
        if not self.enabled:
            return
        try:
            with self._client.start_as_current_generation(
                name=name,
                model=model,
                input=input_messages,
            ) as gen:
                gen.update(
                    output=response.text,
                    usage_details={
                        "input": response.prompt_tokens,
                        "output": response.completion_tokens,
                        "total": response.total_tokens,
                    },
                    metadata=metadata or {},
                )
                if user_id:
                    gen.update_trace(user_id=user_id)
        except Exception:  # noqa: BLE001 — never let tracing break the request
            logger.exception("langfuse trace failed", name=name)

    def flush(self) -> None:
        """Flush buffered traces (safe to call on shutdown)."""
        if not self.enabled:
            return
        try:
            self._client.flush()
        except Exception:  # noqa: BLE001
            logger.exception("langfuse flush failed")


_GLOBAL_SINK: LangfuseSink | None = None


def get_sink() -> LangfuseSink:
    """Return the process-global :class:`LangfuseSink`, creating it lazily."""
    global _GLOBAL_SINK  # noqa: PLW0603 — process-wide singleton
    if _GLOBAL_SINK is None:
        _GLOBAL_SINK = LangfuseSink()
    return _GLOBAL_SINK


@contextmanager
def trace_generation(
    name: str,
    model: str,
    **metadata: Any,
) -> Iterator[dict[str, Any]]:
    """Context manager that emits a Langfuse trace on exit.

    The caller populates ``ctx["input"]`` and ``ctx["response"]`` inside the
    block. When the block exits cleanly, the trace is shipped; exceptions
    propagate unchanged.

    Example::

        with trace_generation("summarise", model="gpt-4o", agent="builtin") as ctx:
            ctx["input"] = prompt
            ctx["response"] = llm.generate(prompt)
    """
    ctx: dict[str, Any] = {"_start": time.monotonic(), "metadata": dict(metadata)}
    try:
        yield ctx
    finally:
        sink = get_sink()
        response = ctx.get("response")
        if sink.enabled and isinstance(response, LLMResponse):
            sink.trace_generation(
                name=name,
                model=model,
                input_messages=ctx.get("input", ""),
                response=response,
                metadata=ctx.get("metadata", {}),
                user_id=ctx.get("user_id"),
            )
