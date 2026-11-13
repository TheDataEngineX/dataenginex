# Decision log

## 0023 - AI services layer (ADR-021, new) (2026-11-12)

Status: accepted (Jay, 2026-11-12).

Context: the vision - TheDataEngineX builds productionized domain
data platforms for SMBs and provides AI services over their Gold
data for insights and growth. The AI stack is the dex repo (Open
WebUI + Ollama + MCP tools + automations), one instance per client.

Decision: AI is a Layer-2 concern and never enters Layer 0. dex's
only data access is the read-only MCP server over `dataenginex
serve` (decision 0020), with row limits and receipt citations on
every answer. Scheduled briefs reuse dex automations (RRULE).
Insight feedback (right / wrong / not useful) is the AI quality
evaluation data. The retail brief from PRODUCT_DESIGN is delivered
by the assistant, not by a dashboard.

Deferred: the LLM serving cost model (API keys vs local GPU vs
hosted vLLM) is undecided until the first paying design partner -
a named trigger.

Consequences: trust machinery (receipts, reconciliation, freshness)
applies to every AI answer. Layer 0 stays a pure data layer; the
v0.7.0 sprawl collapse does not repeat.
