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

from dataenginex.ai.agents import agent_registry
from dataenginex.ai.tools import ToolRegistry, tool_registry
from dataenginex.ai.tools.builtin import register_builtin_tools
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
        register_builtin_tools()

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
        iteration = kwargs.get("iteration", 0)

        if self._llm is None:
            # No LLM — just echo the message and mark done
            return {"done": True, "response": message, "iteration": iteration}

        # Build prompt with tool descriptions
        tool_names = self._tools.list()
        tool_desc = ", ".join(tool_names) if tool_names else "none"

        prompt = (
            f"{self._system_prompt}\n\n"
            f"Available tools: {tool_desc}\n\n"
            f"To use a tool, respond with: TOOL: <name> ARGS: <json_args>\n"
            f"To give a final answer, respond with: ANSWER: <your answer>\n\n"
            f"User: {message}"
        )

        from dataenginex.ai.llm import ChatMessage

        messages = [
            ChatMessage(role="system", content=self._system_prompt),
            *[ChatMessage(role=m["role"], content=m["content"]) for m in self._history],
            ChatMessage(role="user", content=prompt),
        ]

        response = self._llm.chat(messages)
        text = response.text

        # Parse response for tool calls
        if text.startswith("TOOL:"):
            return self._handle_tool_call(text, iteration)

        # Final answer
        answer = text.removeprefix("ANSWER:").strip() if text.startswith("ANSWER:") else text
        return {"done": True, "response": answer, "iteration": iteration}

    def _handle_tool_call(
        self,
        text: str,
        iteration: int,
    ) -> dict[str, Any]:
        """Parse and execute a tool call."""
        import json

        parts = text.split("ARGS:", 1)
        tool_name = parts[0].removeprefix("TOOL:").strip()
        args_str = parts[1].strip() if len(parts) > 1 else "{}"

        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}

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

    @property
    def history(self) -> list[dict[str, str]]:
        """Return conversation history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._history.clear()
