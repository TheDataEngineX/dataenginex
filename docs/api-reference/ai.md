# dataenginex.ai

LLM routing, agent runtimes, vector stores, memory, retrieval, observability, and workflow orchestration.

## Quick import

```python
from dataenginex.ai import (
    ModelRouter, BaseProvider,
    LLMProvider, LLMResponse,
    BuiltinAgentRuntime,
    BuiltinRetriever,
    SandboxConfig,
)
from dataenginex.ai.vectorstore import InMemoryBackend, QdrantBackend, RAGPipeline
```

______________________________________________________________________

## LLM Interface

`dataenginex.ai.llm`

Unified LLM request/response interface across providers. Handles streaming, tool calls, retries, and token counting.

::: dataenginex.ai.llm

**Key classes:** `LLMProvider`, `LLMResponse`, `LLMMessage`, `ToolCall`

```python
from dataenginex.ai.llm import LLMMessage

response = provider.complete([
    LLMMessage(role="user", content="Summarize this dataset."),
])
print(response.content)
```

______________________________________________________________________

## Model Router

`dataenginex.ai.routing.router`

Routes LLM requests to the appropriate provider based on cost, latency, capability, and fallback rules.

::: dataenginex.ai.routing.router

**Key class:** `ModelRouter`

```python
from dataenginex.ai.routing.router import ModelRouter
from dataenginex.ai.routing.anthropic import AnthropicProvider
from dataenginex.ai.routing.ollama import OllamaProvider

router = ModelRouter(providers={"anthropic": AnthropicProvider(), "ollama": OllamaProvider()})
provider = router.route("Explain this error.", complexity="complex")
response = provider.generate("Explain this error.")
```

### Providers

`dataenginex.ai.routing.anthropic` · `dataenginex.ai.routing.openai` · `dataenginex.ai.routing.ollama` · `dataenginex.ai.routing.guarded`

::: dataenginex.ai.routing.anthropic
::: dataenginex.ai.routing.openai
::: dataenginex.ai.routing.ollama
::: dataenginex.ai.routing.guarded

______________________________________________________________________

## Agents

`dataenginex.ai.agents.builtin`

Built-in agent runtime — tool-use loop, memory injection, step tracing, and structured output parsing.

::: dataenginex.ai.agents.builtin

**Key class:** `BuiltinAgentRuntime`

```python
from dataenginex.ai.agents.builtin import BuiltinAgentRuntime

agent = BuiltinAgentRuntime(router=router, tools=[search_tool, sql_tool])
result = agent.run("Find the top 10 customers by revenue last quarter.")
print(result.output)
```

______________________________________________________________________

## Vector Store

`dataenginex.ai.vectorstore`

Embedding storage and similarity search. `InMemoryBackend` (brute-force cosine similarity) is the default; swap in `QdrantBackend` via `dataenginex[qdrant]` for a persistent, production-scale store. `RAGPipeline` combines a backend with an embedding function to support ingest + retrieve.

::: dataenginex.ai.vectorstore

**Key classes:** `InMemoryBackend`, `QdrantBackend`, `RAGPipeline`

```python
from dataenginex.ai.vectorstore import InMemoryBackend, RAGPipeline

rag = RAGPipeline(store=InMemoryBackend(dimension=384))
rag.ingest(["doc1 text", "doc2 text"])
results = rag.query("How do I deploy to K8s?", top_k=3)
```

______________________________________________________________________

## Memory

`dataenginex.ai.memory.base` — abstract memory interface

::: dataenginex.ai.memory.base

`dataenginex.ai.memory.episodic` — short-term conversation memory scoped to a single agent session

::: dataenginex.ai.memory.episodic

`dataenginex.ai.memory.long_term` — persistent memory backed by the vector store, survives across sessions

::: dataenginex.ai.memory.long_term

______________________________________________________________________

## Retrieval

`dataenginex.ai.retrieval.builtin` — RAG retriever: embeds query, searches vector store, returns ranked chunks

::: dataenginex.ai.retrieval.builtin

`dataenginex.ai.retrieval.graph` — graph-based retrieval for structured knowledge graphs

::: dataenginex.ai.retrieval.graph

______________________________________________________________________

## Runtime

`dataenginex.ai.runtime.executor` — async execution engine with concurrency, timeout, and step-level error handling

::: dataenginex.ai.runtime.executor

`dataenginex.ai.runtime.checkpoint` — saves and restores agent run state for long-running or resumable workflows

::: dataenginex.ai.runtime.checkpoint

`dataenginex.ai.runtime.sandbox` — isolated code execution sandbox for agent-generated Python with configurable resource limits

::: dataenginex.ai.runtime.sandbox

______________________________________________________________________

## Tools

`dataenginex.ai.tools.builtin`

Built-in agent tools: `sql_query`, `web_search`, `file_read`, `python_exec`, `vector_search`.

::: dataenginex.ai.tools.builtin

______________________________________________________________________

## Workflows

`dataenginex.ai.workflows.dag` — multi-step agent workflows as DAGs; steps branch, merge, and pass structured outputs

::: dataenginex.ai.workflows.dag

`dataenginex.ai.workflows.conditions` — conditional branching logic for DAG workflows

::: dataenginex.ai.workflows.conditions

`dataenginex.ai.workflows.human_loop` — pause a workflow at a step requiring human review or approval

::: dataenginex.ai.workflows.human_loop

______________________________________________________________________

## Observability

`dataenginex.ai.observability.audit` — logs every LLM request/response, tool call, and agent step for compliance

::: dataenginex.ai.observability.audit

`dataenginex.ai.observability.cost` — tracks token usage and estimated cost per provider, model, and agent run

::: dataenginex.ai.observability.cost

`dataenginex.ai.observability.metrics` — Prometheus metrics for LLM latency, token throughput, error rate

::: dataenginex.ai.observability.metrics
