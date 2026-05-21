"""AI layer — agents, retrieval, tools, routing, runtime, memory, observability, workflows.

Public API::

    from dataenginex.ai import (
        retriever_registry, agent_registry, tool_registry,
        BuiltinRetriever, BuiltinAgentRuntime,
        ModelRouter, BaseProvider,
        Sandbox, SandboxConfig,
        AuditLog, CostTracker,
        AgentDAG, Condition,
        ShortTermMemory, LongTermMemory, EpisodicMemory,
        CheckpointManager, AgentExecutor, AgentConfig,
        AgentMetrics,
    )
"""

from __future__ import annotations

from dataenginex.ai.agents import agent_registry
from dataenginex.ai.agents.builtin import BuiltinAgentRuntime
from dataenginex.ai.llm import (
    ChatMessage,
    LiteLLMProvider,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    MockProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    VLLMProvider,
    get_llm_provider,
)
from dataenginex.ai.memory.base import BaseMemory, MemoryEntry, ShortTermMemory
from dataenginex.ai.memory.episodic import Episode, EpisodicMemory
from dataenginex.ai.memory.long_term import LongTermMemory
from dataenginex.ai.observability.audit import AuditEntry, AuditLog
from dataenginex.ai.observability.cost import CostTracker, TokenUsage
from dataenginex.ai.observability.metrics import AgentMetrics
from dataenginex.ai.retrieval import retriever_registry
from dataenginex.ai.retrieval.builtin import BuiltinRetriever
from dataenginex.ai.routing.router import BaseProvider, ModelRouter
from dataenginex.ai.runtime.checkpoint import Checkpoint, CheckpointManager
from dataenginex.ai.runtime.executor import AgentConfig, AgentExecutor, AgentResponse
from dataenginex.ai.runtime.sandbox import Sandbox, SandboxConfig, SandboxResult
from dataenginex.ai.tools import ToolRegistry, ToolSpec, tool_registry
from dataenginex.ai.vectorstore import (
    Document,
    InMemoryBackend,
    QdrantBackend,
    RAGPipeline,
    SearchResult,
    VectorStoreBackend,
)
from dataenginex.ai.workflows.conditions import Condition
from dataenginex.ai.workflows.dag import AgentDAG
from dataenginex.ai.workflows.human_loop import ApprovalGate

__all__ = [
    # LLM
    "ChatMessage",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "LiteLLMProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "VLLMProvider",
    "get_llm_provider",
    # Vector store
    "Document",
    "InMemoryBackend",
    "QdrantBackend",
    "RAGPipeline",
    "SearchResult",
    "VectorStoreBackend",
    # Registries
    "agent_registry",
    "retriever_registry",
    "tool_registry",
    # Agents
    "BuiltinAgentRuntime",
    "BuiltinRetriever",
    # Tools
    "ToolRegistry",
    "ToolSpec",
    # Memory
    "BaseMemory",
    "MemoryEntry",
    "ShortTermMemory",
    "LongTermMemory",
    "EpisodicMemory",
    "Episode",
    # Observability
    "AuditEntry",
    "AuditLog",
    "CostTracker",
    "TokenUsage",
    "AgentMetrics",
    # Routing
    "BaseProvider",
    "ModelRouter",
    # Runtime
    "AgentConfig",
    "AgentExecutor",
    "AgentResponse",
    "Checkpoint",
    "CheckpointManager",
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    # Workflows
    "AgentDAG",
    "ApprovalGate",
    "Condition",
]
