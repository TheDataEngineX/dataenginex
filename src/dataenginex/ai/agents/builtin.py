"""Built-in agent runtime — tool-calling loop with LLM providers.

Implements a ReAct-style agent loop:
1. Receive user message
2. Ask LLM for response (may include tool calls)
3. Execute tool calls and observe results
4. Repeat until LLM produces final answer or max_iterations reached
"""

from __future__ import annotations

from typing import Any

import structlog

from dataenginex import _json
from dataenginex.ai.agents import agent_registry
from dataenginex.ai.tools import ToolRegistry, tool_registry
from dataenginex.core.interfaces import BaseAgentRuntime
from dataenginex.middleware.domain_metrics import (
    ai_agent_iterations,
    ai_tool_calls_total,
)

logger = structlog.get_logger()


@agent_registry.decorator("builtin", is_default=True)
class BuiltinAgentRuntime(BaseAgentRuntime):
    """Built-in ReAct agent runtime.

    Args:
        llm: An LLM provider instance (from dataenginex.ai.llm).
        system_prompt: System prompt for the agent.
        tools: Tool registry for the agent to use.
        max_iterations: Maximum reasoning steps before stopping.
    """

    def __init__(
        self,
        llm: Any = None,
        system_prompt: str = "You are a helpful data engineering assistant.",
        tools: ToolRegistry | None = None,
        max_iterations: int = 10,
        name: str = "builtin",
        **kwargs: Any,
    ) -> None:
        self._llm = llm
        self._system_prompt = system_prompt
        self._tools = tools or tool_registry
        self._max_iterations = max_iterations
        self._name = name
        self._history: list[dict[str, str]] = []

    async def run(self, message: str, **kwargs: Any) -> dict[str, Any]:
        """Execute agent with message and return structured result.

        Returns dict with 'response' (str), 'iterations' (int), 'tool_calls' (int).
        """
        self._history.append({"role": "user", "content": message})

        tool_calls = 0
        iterations = 0

        for i in range(self._max_iterations):
            iterations = i + 1
            step_result = await self.step(message, iteration=i, **kwargs)

            if step_result.get("done", False):
                response = str(step_result.get("response", ""))
                # Strip raw ReAct trace: extract ANSWER: content if present
                import re as _re

                _ans = _re.search(r"ANSWER:\s*(.+)", response, _re.DOTALL | _re.IGNORECASE)
                if _ans:
                    response = _ans.group(1).strip()
                self._history.append({"role": "assistant", "content": response})
                ai_agent_iterations.labels(agent=self._name).observe(iterations)
                return {"response": response, "iterations": iterations, "tool_calls": tool_calls}

            # If tool was called, continue the loop
            tool_calls += 1
            message = step_result.get("observation", "")

        # Hit max iterations
        final = "I've reached my reasoning limit. Here's what I have so far."
        self._history.append({"role": "assistant", "content": final})
        ai_agent_iterations.labels(agent=self._name).observe(self._max_iterations)
        return {"response": final, "iterations": self._max_iterations, "tool_calls": tool_calls}

    async def step(self, message: str, **kwargs: Any) -> dict[str, Any]:
        """Execute one reasoning step."""
        import re

        iteration = kwargs.get("iteration", 0)

        if self._llm is None:
            return {"done": True, "response": message, "iteration": iteration}

        tool_names = self._tools.list()
        tool_desc = ", ".join(tool_names) if tool_names else "none"

        prompt = (
            f"Available tools: {tool_desc}\n\n"
            f"You MUST respond in EXACTLY one of these two formats — no other text:\n"
            f'  TOOL: <tool_name>\n  ARGS: {{"key": "value"}}\n\n'
            f"  ANSWER: <your final answer>\n\n"
            f"Example tool call:\n"
            f'  TOOL: query\n  ARGS: {{"sql": "SELECT * FROM gold_top_movies LIMIT 3"}}\n\n'
            f"User request: {message}"
        )

        from dataenginex.ai.llm import ChatMessage

        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *[ChatMessage(role=m["role"], content=m["content"]) for m in self._history],
            ChatMessage(role="user", content=prompt),
        ]

        response = self._llm.chat(messages)
        text = response.text.strip()

        # Robust: search for TOOL: pattern anywhere in text
        tool_match = re.search(
            r"TOOL:\s*(\w+)\s*\n?\s*ARGS:\s*(\{.*?\})",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if tool_match:
            tool_name = tool_match.group(1).strip()
            args_str = tool_match.group(2).strip()
            try:
                args = _json.loads(args_str)
            except ValueError:
                args = {}
            return self._handle_tool_call_parsed(tool_name, args, iteration)

        # Final answer — strip ANSWER: prefix if present
        answer = re.sub(r"^ANSWER:\s*", "", text, flags=re.IGNORECASE).strip()
        return {"done": True, "response": answer, "iteration": iteration}

    def _handle_tool_call_parsed(
        self,
        tool_name: str,
        args: dict[str, Any],
        iteration: int,
    ) -> dict[str, Any]:
        """Execute a parsed tool call."""
        try:
            result = self._tools.call(tool_name, **args)
            observation = f"Tool '{tool_name}' returned: {result}"
            ai_tool_calls_total.labels(tool=tool_name, status="ok").inc()
        except Exception as e:
            observation = f"Tool '{tool_name}' failed: {e}"
            ai_tool_calls_total.labels(tool=tool_name, status="error").inc()

        self._history.append(
            {"role": "assistant", "content": f"[tool: {tool_name}] {observation}"},
        )
        return {
            "done": False,
            "tool": tool_name,
            "args": args,
            "observation": observation,
            "iteration": iteration,
        }

    def _handle_tool_call(
        self,
        text: str,
        iteration: int,
    ) -> dict[str, Any]:
        """Parse and execute a tool call from raw TOOL:/ARGS: text."""

        parts = text.split("ARGS:", 1)
        tool_name = parts[0].removeprefix("TOOL:").strip()
        args_str = parts[1].strip() if len(parts) > 1 else "{}"
        try:
            args = _json.loads(args_str)
        except ValueError:
            args = {}
        return self._handle_tool_call_parsed(tool_name, args, iteration)

    @property
    def history(self) -> list[dict[str, str]]:
        """Return conversation history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()
