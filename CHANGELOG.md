# Changelog

All notable changes to `dataenginex` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.4.0 — Scope reset (2026-05-25)

Versions 1.0.0 – 1.1.2 were prematurely tagged stable. Resetting to `0.4.0` to honestly reflect pre-1.0 maturity. The full strategic rationale lives in [ADR-0007](https://github.com/TheDataEngineX/docs/blob/main/adr/0007-local-first-scope-reset.md) and the 2026 implementation roadmap at [docs/roadmap/DESIGN-2026.md](https://github.com/TheDataEngineX/docs/blob/main/docs/roadmap/DESIGN-2026.md).

The 1.x versions on PyPI are yanked but remain installable by exact pin (`pip install 'dataenginex==1.1.2'`); plain `pip install dataenginex` now resolves to `0.4.0`.

### Why

The 1.x versions were published before the project had:

- A confirmed product positioning (now: local-first Data + ML + AI workbench for individuals and small teams)
- A stable public API surface
- User feedback validating the design.

### When we'll reach 1.0

- ≥ 100 weekly active installs
- Public API frozen for 3 releases without breakage
- v0.5 launch feedback incorporated
- End-to-end demo flow polished

### Breaking changes

- `asyncpg`, `redis`, `qdrant-client`, `arq` moved out of base dependencies into optional extras `[postgres]`, `[qdrant]`, `[queue]`. Install only what you need.
- `dataenginex.ai.routing.HuggingFaceProvider` removed (HF inference API graveyard).
- `dataenginex.ai.observability.langfuse` and the `[observability]` optional-dependency extra removed (contradicts local-first positioning; pipe via OpenLineage to Marquez/DataHub if needed).
- `dataenginex.ai.runtime.sandbox.Sandbox` now emits `ExperimentalFeatureWarning` on first use per process. Silence with `warnings.filterwarnings("ignore", category=ExperimentalFeatureWarning)`. Subprocess sandbox is **not** safe for adversarial untrusted code — use containers/VMs for that.
- Routing default for `"simple"` complexity changed from `"huggingface"` to `"ollama"`.

### Documentation

- New [ADR-0007 — Local-first scope reset](https://github.com/TheDataEngineX/docs/blob/main/adr/0007-local-first-scope-reset.md) supersedes ADR-0002 (CareerDEX spinout), ADR-0003 (Reflex migration), and ADR-0006 (12-week enterprise transformation roadmap).
- New 10-week implementation roadmap at [docs/roadmap/DESIGN-2026.md](https://github.com/TheDataEngineX/docs/blob/main/docs/roadmap/DESIGN-2026.md) covering Phase 1 (foundation cleanup) through Phase 4 (demo launch).

### Migration from 1.1.x

1. Update install: `pip install 'dataenginex[postgres,qdrant,queue]'` if you need any of those backends (or omit for the lean default).
1. Replace `HuggingFaceProvider` with `OllamaProvider` (local) or `OpenAIProvider` (cloud).
1. Remove any `langfuse` imports; cost tracking remains via `dataenginex.ai.observability.cost`.
1. If you call `Sandbox()`, expect a one-time warning per process; suppress as shown above if running in scripts.

## [1.1.1](https://github.com/TheDataEngineX/dex/compare/v1.1.0...v1.1.1) (2026-05-07)

### Bug Fixes

- rich reflex compat ([#232](https://github.com/TheDataEngineX/dex/issues/232)) ([#233](https://github.com/TheDataEngineX/dex/issues/233)) ([7d33c05](https://github.com/TheDataEngineX/dex/commit/7d33c05d9d3b041567a5539930dabc30294a0d8d))

## [1.1.0](https://github.com/TheDataEngineX/dex/compare/v1.0.3...v1.1.0) (2026-05-06)

### Features

- add /ready endpoint and fix Docker runtime; make semgrep non-blocking ([b986a89](https://github.com/TheDataEngineX/dex/commit/b986a899565f469b1d2262e4b89824ab91a06a31))
- add GitHub-based project management and SDLC templates ([#13](https://github.com/TheDataEngineX/dex/issues/13)) ([eac3683](https://github.com/TheDataEngineX/dex/commit/eac368356767997b9a7a3cbdcd4e6f5722723761))
- add GitOps infrastructure with ArgoCD and Kustomize ([db4479f](https://github.com/TheDataEngineX/dex/commit/db4479f85724798dc162b0215c24deb0a9860453))
- Add Prometheus metrics and OpenTelemetry tracing ([#29](https://github.com/TheDataEngineX/dex/issues/29)) ([c1c9a7e](https://github.com/TheDataEngineX/dex/commit/c1c9a7ed562929c5e7a0effc212cd7e43ff0bb5f))
- Add structured logging with request ID tracking ([#21](https://github.com/TheDataEngineX/dex/issues/21)) ([118b259](https://github.com/TheDataEngineX/dex/commit/118b259e7f18f991451fa2dd4dddb7351e848c3a))
- add v0.2.0 Production Hardening features ([#56](https://github.com/TheDataEngineX/dex/issues/56)) ([f45982d](https://github.com/TheDataEngineX/dex/commit/f45982dd4898753f8130fcf1156cd3fe836c701f))
- add validation and error handling ([#52](https://github.com/TheDataEngineX/dex/issues/52)) ([5d06b81](https://github.com/TheDataEngineX/dex/commit/5d06b819b21f62c33a86626098a8f0f9d27440cc))
- add workflow_dispatch to release-dataenginex.yml ([#161](https://github.com/TheDataEngineX/dex/issues/161)) ([a9d2480](https://github.com/TheDataEngineX/dex/commit/a9d2480a8fef404e607b20c2beb028a465d7028c))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, and docs overhaul ([#138](https://github.com/TheDataEngineX/dex/issues/138)) ([1f544c9](https://github.com/TheDataEngineX/dex/commit/1f544c9bbb1e39c20ac291534b7cc682da01a1c3))
- CareerDEX v0.5.0 — domain extraction, plugin system, ML modules, docs overhaul ([1f544c9](https://github.com/TheDataEngineX/dex/commit/1f544c9bbb1e39c20ac291534b7cc682da01a1c3))
- clean public API surface & stabilize exports ([#86](https://github.com/TheDataEngineX/dex/issues/86)) ([#126](https://github.com/TheDataEngineX/dex/issues/126)) ([de539be](https://github.com/TheDataEngineX/dex/commit/de539bec139cb24e18b75422a31cec22ad394e9f))
- dataenginex 0.6.1 — RAG/LLM wiring, Node.js 24 actions ([#159](https://github.com/TheDataEngineX/dex/issues/159)) ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- dataenginex 0.7.0 — MLflow 3.x, cloud SDKs optional, dep bumps ([#173](https://github.com/TheDataEngineX/dex/issues/173)) ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- DataEngineX 1.0 — Phases 1-5 (Data + ML + AI + API + Infra) ([#198](https://github.com/TheDataEngineX/dex/issues/198)) ([525c3c9](https://github.com/TheDataEngineX/dex/commit/525c3c9c0107158cbce81832f6a71287f8f037f2))
- dex studio direct import ([#202](https://github.com/TheDataEngineX/dex/issues/202)) ([1844ef5](https://github.com/TheDataEngineX/dex/commit/1844ef5d55b6023e8400c4ddc85ab09503ec223d))
- docs cleanup ([f4eff14](https://github.com/TheDataEngineX/dex/commit/f4eff14a1aeed657b715b182ac495c920f7b701f))
- docs notify ([#210](https://github.com/TheDataEngineX/dex/issues/210)) ([c36616d](https://github.com/TheDataEngineX/dex/commit/c36616d9d0ae7a97274bd40ea41f39bc26f68fe0))
- enhance health probes and readiness checks ([#43](https://github.com/TheDataEngineX/dex/issues/43)) ([ddd3031](https://github.com/TheDataEngineX/dex/commit/ddd3031e9999451684babdb8c71f81bb0a4877d7))
- enterprise auth, RBAC, SCIM, LiteLLM/vLLM, Langfuse, domain met… ([#223](https://github.com/TheDataEngineX/dex/issues/223)) ([abeb1cc](https://github.com/TheDataEngineX/dex/commit/abeb1cc28a14745b8a9c6d6f040c0cd525ead23a))
- flatten workspace, strip legacy tooling, add examples 07-10, pre-commit fixes ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- **ml:** add MLflowModelRegistry and fix example 10 drift call ([#168](https://github.com/TheDataEngineX/dex/issues/168)) ([d689582](https://github.com/TheDataEngineX/dex/commit/d6895828f9ef652ce45e2dd7d4fd5ab8422093fe))
- P1-high issues [#87](https://github.com/TheDataEngineX/dex/issues/87) [#88](https://github.com/TheDataEngineX/dex/issues/88) [#89](https://github.com/TheDataEngineX/dex/issues/89) [#92](https://github.com/TheDataEngineX/dex/issues/92) [#93](https://github.com/TheDataEngineX/dex/issues/93) — storage, ML serving, drift scheduler, docstrings ([#128](https://github.com/TheDataEngineX/dex/issues/128)) ([0b003e0](https://github.com/TheDataEngineX/dex/commit/0b003e0e5cbe24f417905171eb3971c88ee492e3))
- Phase 0 foundation — config system, backend registry, interfaces, CLI, exceptions ([#197](https://github.com/TheDataEngineX/dex/issues/197)) ([a0e24cd](https://github.com/TheDataEngineX/dex/commit/a0e24cd567b517c2162a3050a94251cb3bc2c61f))
- Phases 1-6A — data layer, ML/AI, API factory, engine integration ([#199](https://github.com/TheDataEngineX/dex/issues/199)) ([01c9911](https://github.com/TheDataEngineX/dex/commit/01c991115aa37e21ff43e28285c66ff780f8ebf4))
- quality schema spark audit ([#212](https://github.com/TheDataEngineX/dex/issues/212)) ([2965801](https://github.com/TheDataEngineX/dex/commit/2965801257f6949a48f1c59be2f88e92294b4691))
- RAG/LLM wiring + bump GitHub Actions to Node.js 24 ([#156](https://github.com/TheDataEngineX/dex/issues/156)) ([5912d38](https://github.com/TheDataEngineX/dex/commit/5912d38f3b5af9ba8fbccaea0fac8fde47159c9c))
- RAG/LLM wiring + bump GitHub Actions to Node.js 24 ([#157](https://github.com/TheDataEngineX/dex/issues/157)) ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- **secops:** add PII detection, masking, and audit logging module ([#169](https://github.com/TheDataEngineX/dex/issues/169)) ([5a2269c](https://github.com/TheDataEngineX/dex/commit/5a2269c67fef1e64d1bc9c0431eb692fe06f688c))
- upgrade to MLflow 3.x, move cloud SDKs to optional extra, bump all dep floors ([#172](https://github.com/TheDataEngineX/dex/issues/172)) ([717f760](https://github.com/TheDataEngineX/dex/commit/717f760eec68aa47548723e68b513fe8b10c755e))
- v0.3.0 production hardening ([#76](https://github.com/TheDataEngineX/dex/issues/76)) ([0f019fa](https://github.com/TheDataEngineX/dex/commit/0f019face69b9923db87e71c911d757455c70f5f))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([77f6984](https://github.com/TheDataEngineX/dex/commit/77f6984b7ad39cf01f0e65b278821852464f0c9e))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([bb818ef](https://github.com/TheDataEngineX/dex/commit/bb818efd3dacef813effb4dca52c34010282dcd2))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([8cc5b2b](https://github.com/TheDataEngineX/dex/commit/8cc5b2be0e87d05f703c5345dfe61f1e95c851aa))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([75c187b](https://github.com/TheDataEngineX/dex/commit/75c187b2fbdba2f52b21ab80ae0881cdea91029f))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([ae0bd44](https://github.com/TheDataEngineX/dex/commit/ae0bd446c67e1e2254308f9c895e3a3652968810))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([3d86fc7](https://github.com/TheDataEngineX/dex/commit/3d86fc78d2774fb3182b11e087ffd5aacd4ce361))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([9ed4e19](https://github.com/TheDataEngineX/dex/commit/9ed4e196834b7f3a4fe8a12b4a4ab845303e5f09))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([62b2e58](https://github.com/TheDataEngineX/dex/commit/62b2e58407f25549fd249bfacb399610454998b9))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([a987b8a](https://github.com/TheDataEngineX/dex/commit/a987b8a5e9f9c9f4dd8801f424fd8e64ca6aa1c3))
- v0.3.2 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79))\\n\\nImplements all 6 DEX module epics ([#37](https://github.com/TheDataEngineX/dex/issues/37)-[#42](https://github.com/TheDataEngineX/dex/issues/42)) plus 9 project-wide improvements.\\n77 files changed, 4640 insertions, 143 deletions.\\n233 tests passing, 0 lint/mypy errors.\\n\\nCloses [#37](https://github.com/TheDataEngineX/dex/issues/37), closes [#38](https://github.com/TheDataEngineX/dex/issues/38), closes [#39](https://github.com/TheDataEngineX/dex/issues/39), closes [#40](https://github.com/TheDataEngineX/dex/issues/40), closes [#41](https://github.com/TheDataEngineX/dex/issues/41), closes [#42](https://github.com/TheDataEngineX/dex/issues/42) ([bcbed5c](https://github.com/TheDataEngineX/dex/commit/bcbed5c5017ec67f57c63d575b11314a968f2c04))
- v0.4.0 — DEX Module Epics & Project-Wide Improvements ([#79](https://github.com/TheDataEngineX/dex/issues/79)) ([bcbed5c](https://github.com/TheDataEngineX/dex/commit/bcbed5c5017ec67f57c63d575b11314a968f2c04))

### Bug Fixes

- add --no-root to poetry install and fix workflow permissions ([58c8636](https://github.com/TheDataEngineX/dex/commit/58c86360003308e2dfa1bf58bfc92a20fffa89e5))
- add explicit strict=False to zip() calls in ml_utils and train_model ([5bcc790](https://github.com/TheDataEngineX/dex/commit/5bcc79072fce047f3fcd921d1e1a6ed2ecbf76f8))
- add last-release-sha to anchor release-please at v0.9.9 ([7e78ca2](https://github.com/TheDataEngineX/dex/commit/7e78ca203347ff4c4000ca6ec42c335650da1b86))
- add login step for GitHub Container Registry in CD workflow ([2f59d72](https://github.com/TheDataEngineX/dex/commit/2f59d726d1b99680378f748a0fa479652934c733))
- add missing Readme.md and src/ to Docker build context ([4b2355f](https://github.com/TheDataEngineX/dex/commit/4b2355f13724f9de3292b838ae4549e7d1fdc271))
- add registry prefix to image name in kustomization ([c402704](https://github.com/TheDataEngineX/dex/commit/c40270466aff1eaee5346d307ea90a779e5fe986))
- add setup-uv to release workflow (uvx was missing for SBOM generation) ([2c3a9f2](https://github.com/TheDataEngineX/dex/commit/2c3a9f25f61f3e3ab6c7fd6f92e2640836cb8c16))
- allow PyPI publish on release workflow completion ([#120](https://github.com/TheDataEngineX/dex/issues/120)) ([f7b6bd4](https://github.com/TheDataEngineX/dex/commit/f7b6bd4f775814093a5f9a287ff5cdcbd80e6f67))
- always push both latest and sha-\<short_sha> tags for Docker image ([#101](https://github.com/TheDataEngineX/dex/issues/101)) ([b7f63e4](https://github.com/TheDataEngineX/dex/commit/b7f63e40e161ce5bfb550bae0526ad40dd934a88))
- apache-airflow\<3.0.0 — resolve 8 Dependabot security alerts + sync dev ([#162](https://github.com/TheDataEngineX/dex/issues/162)) ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- apply Ruff import-order fixes for CI lint ([d597c5e](https://github.com/TheDataEngineX/dex/commit/d597c5e5df2f1e2f9c09d98e7db2dfb340cce66f))
- boost test coverage to 83%+ (feature → dev) ([#140](https://github.com/TheDataEngineX/dex/issues/140)) ([71057ce](https://github.com/TheDataEngineX/dex/commit/71057ce631a6bae39c105ea751002792e69547b0))
- CD Bug Fix ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- CD Bug Fix ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- CD Bug Fix ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- CD Bug Fix ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- CD Bug Fix ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- CD Bug Fix ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- CD Bug Fix ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- CD Bug Fix ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- CD Bug Fix ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- CD Bug Fix ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- CD Bug Fix ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- CD Bug Fix ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- CD Bug Fix ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- CD Bug Fix ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- CD Bug Fix ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- CD Bug Fix ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- CD Bug Fix ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- CD Bug Fix ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- CD Bug Fix ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- CD Bug Fix ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- CD Bug Fix ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- CD Bug Fix ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- CD Bug Fix ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- CD Bug Fix ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- CD Bug Fix ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- CD Bug Fix ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- CD Bug Fix ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- CD Bug Fix ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- CD Bug Fix ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- CD Bug Fix ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- CD Bug Fix ([77f6984](https://github.com/TheDataEngineX/dex/commit/77f6984b7ad39cf01f0e65b278821852464f0c9e))
- CD Bug Fix ([bb818ef](https://github.com/TheDataEngineX/dex/commit/bb818efd3dacef813effb4dca52c34010282dcd2))
- CD Bug Fix ([0342ac3](https://github.com/TheDataEngineX/dex/commit/0342ac33795aba430c4b9569a1080d8f5564d90f))
- CD workflow git authentication using GH_TOKEN ([03216e2](https://github.com/TheDataEngineX/dex/commit/03216e24ab842c5e54a3102d515fb7546cbba45e))
- CD workflow permissions and token persistence ([#58](https://github.com/TheDataEngineX/dex/issues/58)) ([c63aa0c](https://github.com/TheDataEngineX/dex/commit/c63aa0c077fab637952ce5e2cd9f5a5493a873b6))
- cd.yml - correct Trivy image reference construction ([#100](https://github.com/TheDataEngineX/dex/issues/100)) ([1b59c5b](https://github.com/TheDataEngineX/dex/commit/1b59c5b820946b0769faa0f447c74b1fb8ebb8fe))
- compute lowercase image name for GitHub Container Registry ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- compute lowercase image name for GitHub Container Registry ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- compute lowercase image name for GitHub Container Registry ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- compute lowercase image name for GitHub Container Registry ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- compute lowercase image name for GitHub Container Registry ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- compute lowercase image name for GitHub Container Registry ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- compute lowercase image name for GitHub Container Registry ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- compute lowercase image name for GitHub Container Registry ([7fde841](https://github.com/TheDataEngineX/dex/commit/7fde841875d35e870bafd8a2078521e5e3398652))
- compute lowercase image name for GitHub Container Registry ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- compute lowercase image name for GitHub Container Registry ([97ea59d](https://github.com/TheDataEngineX/dex/commit/97ea59dc0e37eb2a780a4c45419f2704f2efbe1d))
- compute lowercase image name for GitHub Container Registry ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- compute lowercase image name for GitHub Container Registry ([5ed7384](https://github.com/TheDataEngineX/dex/commit/5ed7384553fecaaba91c4b5b5125c8502d902ae9))
- compute lowercase image name for GitHub Container Registry ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- compute lowercase image name for GitHub Container Registry ([4e0f5a3](https://github.com/TheDataEngineX/dex/commit/4e0f5a37099fb249d1e0a1906a28a508c942546a))
- compute lowercase image name for GitHub Container Registry ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- compute lowercase image name for GitHub Container Registry ([946ee71](https://github.com/TheDataEngineX/dex/commit/946ee719e370ff311eb549e56620aaefb8127a25))
- compute lowercase image name for GitHub Container Registry ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- compute lowercase image name for GitHub Container Registry ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- compute lowercase image name for GitHub Container Registry ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- compute lowercase image name for GitHub Container Registry ([b7edeb2](https://github.com/TheDataEngineX/dex/commit/b7edeb270786648853a6e9b9ffab2de86fcad3a6))
- compute lowercase image name for GitHub Container Registry ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- compute lowercase image name for GitHub Container Registry ([73a0606](https://github.com/TheDataEngineX/dex/commit/73a06061eaa220d550d0496feb5795e2c5455b6a))
- compute lowercase image name for GitHub Container Registry ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- compute lowercase image name for GitHub Container Registry ([d475471](https://github.com/TheDataEngineX/dex/commit/d475471dbedbf3ad9f2e0d5afe76c178d3b8e854))
- compute lowercase image name for GitHub Container Registry ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- compute lowercase image name for GitHub Container Registry ([aa5665c](https://github.com/TheDataEngineX/dex/commit/aa5665c4a6413e5150425a2b205bc43188966bfd))
- compute lowercase image name for GitHub Container Registry ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- compute lowercase image name for GitHub Container Registry ([6032650](https://github.com/TheDataEngineX/dex/commit/6032650b5754012c5a1dba951544004eb3eb5f2b))
- compute lowercase image name for GitHub Container Registry ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- compute lowercase image name for GitHub Container Registry ([458223e](https://github.com/TheDataEngineX/dex/commit/458223e6fa9d0c26ec80a25731afa01a15a27335))
- compute lowercase image name for GitHub Container Registry ([77f6984](https://github.com/TheDataEngineX/dex/commit/77f6984b7ad39cf01f0e65b278821852464f0c9e))
- compute lowercase image name for GitHub Container Registry ([bb818ef](https://github.com/TheDataEngineX/dex/commit/bb818efd3dacef813effb4dca52c34010282dcd2))
- compute lowercase image name for GitHub Container Registry ([c04e944](https://github.com/TheDataEngineX/dex/commit/c04e9443f3579f14c6fe5dc0e5ddfed51d90f9f2))
- compute lowercase image name for GitHub Container Registry ([25f796b](https://github.com/TheDataEngineX/dex/commit/25f796b7dbe20ebdfa0d23c630fb0dd387e8e9d1))
- continue CI/CD hardening after merged PR [#107](https://github.com/TheDataEngineX/dex/issues/107) ([#108](https://github.com/TheDataEngineX/dex/issues/108)) ([8cc5b2b](https://github.com/TheDataEngineX/dex/commit/8cc5b2be0e87d05f703c5345dfe61f1e95c851aa))
- copy LICENSE into Docker build context for Poetry Core ([7e230f8](https://github.com/TheDataEngineX/dex/commit/7e230f855023b521f2b78e0107e1a93fb5b35cbd))
- correct import order for ruff isort ([32815a6](https://github.com/TheDataEngineX/dex/commit/32815a6fbddcf3ba01019ff2ba79bb70e6a9367b))
- cyclonedx-bom 7+ flags (-o/--of), remove redundant setup-python, bump github-script@v8 ([b7dfae3](https://github.com/TheDataEngineX/dex/commit/b7dfae3db2ed22dd14a6dd150999083a2a1c1568))
- dependabot targets dev branch, not main; bump 0.8.3 ([f1c1fd2](https://github.com/TheDataEngineX/dex/commit/f1c1fd2134bae0997def39ce7c518c9c71265382))
- dependabot targets dev branch, not main; bump 0.8.3 ([#180](https://github.com/TheDataEngineX/dex/issues/180)) ([67128a1](https://github.com/TheDataEngineX/dex/commit/67128a1ebd0ab56cc4c4aa19811e6f14a318dec3))
- dependabot targets dev branch, not main; bump 0.8.3 ([#186](https://github.com/TheDataEngineX/dex/issues/186)) ([bcab350](https://github.com/TheDataEngineX/dex/commit/bcab3509852f65f6e38f57c2e0212bb81fee798b))
- dex-prod namespace in ApplicationSet should be dex-prod ([c835f55](https://github.com/TheDataEngineX/dex/commit/c835f556d87f881b5df529f3ccf177c1002b9fdc))
- exclude pipelines directory from ruff checks in pyproject.toml ([ab3e304](https://github.com/TheDataEngineX/dex/commit/ab3e30435e35a6074e9f43914dcfaf0991356661))
- harden CI/CD security and deployment workflows ([#109](https://github.com/TheDataEngineX/dex/issues/109)) ([bb818ef](https://github.com/TheDataEngineX/dex/commit/bb818efd3dacef813effb4dca52c34010282dcd2))
- harden CI/CD workflows and add poe actionlint task ([#107](https://github.com/TheDataEngineX/dex/issues/107)) ([75c187b](https://github.com/TheDataEngineX/dex/commit/75c187b2fbdba2f52b21ab80ae0881cdea91029f))
- improve Slack notification error handling and ensure webhook is set ([974743e](https://github.com/TheDataEngineX/dex/commit/974743e2d9a344936909f5b183a9afc2dfa53b9e))
- limit ruff check to src and tests directories ([176f887](https://github.com/TheDataEngineX/dex/commit/176f887b40e81e1de8bcaa9b56384d8e72e39b60))
- mlflow 3.x alias API, release workflow trigger, bump 0.7.1 ([f1cb762](https://github.com/TheDataEngineX/dex/commit/f1cb762a17beef80cb033d486e5b7419df0de202))
- mlflow 3.x alias API, release workflow trigger, bump 0.7.1 ([2b6da25](https://github.com/TheDataEngineX/dex/commit/2b6da25c3c94873cbec64607ce510fc5b835413e))
- pin apache-airflow\<3.0.0 to resolve 8 Dependabot security alerts ([#160](https://github.com/TheDataEngineX/dex/issues/160)) ([c5f49de](https://github.com/TheDataEngineX/dex/commit/c5f49de1780a7f94042f1700e0694e4cfba94fd7))
- prod namespace should be dex-prod not dex ([2cc5664](https://github.com/TheDataEngineX/dex/commit/2cc5664ac58792710b8bc11de2da74f7798b9754))
- pypi-publish uses Python 3.13 via setup-uv; release workflow auto-triggers publish ([c6ffb62](https://github.com/TheDataEngineX/dex/commit/c6ffb62ae4012403a206e075e7d69b9c61f5bd0f))
- reduce CD duplicate workflow_run triggers ([#123](https://github.com/TheDataEngineX/dex/issues/123)) ([e16cc24](https://github.com/TheDataEngineX/dex/commit/e16cc2425ccd2c76ac22d9706f7abc0a284ac39d))
- release workflow, single version source, poe install → uv ([#81](https://github.com/TheDataEngineX/dex/issues/81)) ([62b2e58](https://github.com/TheDataEngineX/dex/commit/62b2e58407f25549fd249bfacb399610454998b9))
- remove codeql job from security.yml (conflicts with GitHub default setup) ([53826aa](https://github.com/TheDataEngineX/dex/commit/53826aa4874a45f0d5319a1b0c9ce7cb1388ef68))
- remove conflicting pytest addopts configuration ([91f62d0](https://github.com/TheDataEngineX/dex/commit/91f62d013d37cb720be59238ffc7b11ef5c5d505))
- remove invalid pip cache from setup-python step ([ae6affc](https://github.com/TheDataEngineX/dex/commit/ae6affc24994d7abf642c49d778dd82ae4d36e1b))
- remove Kustomize version spec and add Namespace whitelist ([c587cba](https://github.com/TheDataEngineX/dex/commit/c587cba90acb53fad6525a19f6d1895314f5315d))
- remove preview-deploy.yml and fix docs-pages enablement ([eca077a](https://github.com/TheDataEngineX/dex/commit/eca077ab9e0896e53038071d7685d9539c759e66))
- remove preview-deploy.yml and fix docs-pages enablement ([#115](https://github.com/TheDataEngineX/dex/issues/115)) ([b0c5c95](https://github.com/TheDataEngineX/dex/commit/b0c5c951fba6f245eb9d835fb4eadb13a4305b14))
- remove unused exception variable in auth middleware (F841) ([8e9f116](https://github.com/TheDataEngineX/dex/commit/8e9f1160dbe403e262c23bd928cc73db221bc01d))
- resolve merge conflict in examples/04_ml_training.py ([2da9106](https://github.com/TheDataEngineX/dex/commit/2da91069cff6257ebd6f65be3adace655eb14e18))
- resolve YAML syntax error in CI workflow with proper formatting ([17bd282](https://github.com/TheDataEngineX/dex/commit/17bd28206245881273742e9cbe3a835d04e05356))
- restore pypi-publish, release, and security CI/CD workflows ([#155](https://github.com/TheDataEngineX/dex/issues/155)) ([0a6fe2a](https://github.com/TheDataEngineX/dex/commit/0a6fe2a495d2d9643844fd9ca03a4b308f31513d))
- restore pypi-publish, release, and security workflows ([#154](https://github.com/TheDataEngineX/dex/issues/154)) ([fb7a242](https://github.com/TheDataEngineX/dex/commit/fb7a24210940bdf20cbf72de7bb776d54c3db8c4))
- restructure release-please-config to packages format with last-release-sha ([46f0b69](https://github.com/TheDataEngineX/dex/commit/46f0b69b8372d54d26ba60eedd9095d7fb0f6cd3))
- rich pin reflex compatibility ([#225](https://github.com/TheDataEngineX/dex/issues/225)) ([7d2673d](https://github.com/TheDataEngineX/dex/commit/7d2673daa12f73fe08e3b0c650bb17a7a2c46c26))
- rich pin reflex compatibility ([#225](https://github.com/TheDataEngineX/dex/issues/225)) ([9026174](https://github.com/TheDataEngineX/dex/commit/9026174fd41675cef105d45bec9af35194182d4f))
- skip trusted publish on manual workflow dispatch ([f812128](https://github.com/TheDataEngineX/dex/commit/f812128cfd0ae04c381dfc0a191f0924e9ada9e2))
- stabilize main CD gating and release-triggered PyPI fallback ([#119](https://github.com/TheDataEngineX/dex/issues/119)) ([6b12108](https://github.com/TheDataEngineX/dex/commit/6b12108eebecfee2bfb04ab4c4285fc920a51bfc))
- sync dev to main ([40d5dff](https://github.com/TheDataEngineX/dex/commit/40d5dff99ae4295599badc848cd530df6eff9ffb))
- trigger pypi publish on release published events ([9cbe52c](https://github.com/TheDataEngineX/dex/commit/9cbe52c56c05c95982c466c3045bef2610d5a86f))
- update CD to use PRs for manifest updates ([#44](https://github.com/TheDataEngineX/dex/issues/44)) ([af95a41](https://github.com/TheDataEngineX/dex/commit/af95a41712bd5d20cfe019d7be62bcbb435cb3e8))
- update dependencies and GitHub Actions versions ([0ee7c51](https://github.com/TheDataEngineX/dex/commit/0ee7c5151d343f5d68204059997d933993aa1230))
- update release-please manifest to 1.0.3 ([a565e47](https://github.com/TheDataEngineX/dex/commit/a565e47d17ffa37c1665a3b959b2365d67728a8a))
- update ruff configuration to use lint section ([e8d85bf](https://github.com/TheDataEngineX/dex/commit/e8d85bf718fcbed6ad9d3ca7d4620a57aa3ff4a4))
- Update stage and prod to use ghcr.io registry and sha-03216e24 image tag ([88e3599](https://github.com/TheDataEngineX/dex/commit/88e35999f0d3ab33527cb09cf64ab9cc3c4049ed))
- use vars-based environments for pypi trusted publishing ([5b55b42](https://github.com/TheDataEngineX/dex/commit/5b55b42ec23872eb9121cf45fb1beace89d4d700))
- v0.3.1 Infrastructure Alignment ([#78](https://github.com/TheDataEngineX/dex/issues/78)) ([829e5eb](https://github.com/TheDataEngineX/dex/commit/829e5ebfee1c8d6e3b5ae880684408fa9b915317))
- **v0.3.3:** CD & Security Slack notification conditions ([3464c5c](https://github.com/TheDataEngineX/dex/commit/3464c5cc1e47fa895aed91b7bc7cd753cf74f013))

### Documentation

- add CHANGELOG entry for 0.7.1 ([fbc5887](https://github.com/TheDataEngineX/dex/commit/fbc5887a35cce3158d59506f40f11a18c304b0ec))
- add CHANGELOG entry for 0.7.1 ([c434c39](https://github.com/TheDataEngineX/dex/commit/c434c393d352e0a94ff8d0876b9c223902d81539))
- add comprehensive project architecture and phased roadmap ([#20](https://github.com/TheDataEngineX/dex/issues/20)) ([081f156](https://github.com/TheDataEngineX/dex/commit/081f156d8910f25c187849e226977177148579a8))
- consolidate and streamline documentation for developer onboarding ([#12](https://github.com/TheDataEngineX/dex/issues/12)) ([d7725c4](https://github.com/TheDataEngineX/dex/commit/d7725c4d5188e66ffe39174fb43329bad952f75f))
- docs cleanup ([#211](https://github.com/TheDataEngineX/dex/issues/211)) ([0a6b7f7](https://github.com/TheDataEngineX/dex/commit/0a6b7f70287eb7399eb17acea2fb0ad09efd0597))
- enhance OpenAPI and examples ([#53](https://github.com/TheDataEngineX/dex/issues/53)) ([7759e5f](https://github.com/TheDataEngineX/dex/commit/7759e5f215bd98d4ecfbf0922928fd04025e4642))

## [0.10.0](https://github.com/TheDataEngineX/dex/compare/v0.9.9...v0.10.0) (2026-04-01)

### Features

- docs cleanup ([f4eff14](https://github.com/TheDataEngineX/dex/commit/f4eff14a1aeed657b715b182ac495c920f7b701f))
- docs notify ([#210](https://github.com/TheDataEngineX/dex/issues/210)) ([c36616d](https://github.com/TheDataEngineX/dex/commit/c36616d9d0ae7a97274bd40ea41f39bc26f68fe0))
- quality schema spark audit ([#212](https://github.com/TheDataEngineX/dex/issues/212)) ([2965801](https://github.com/TheDataEngineX/dex/commit/2965801257f6949a48f1c59be2f88e92294b4691))

### Bug Fixes

- add last-release-sha to anchor release-please at v0.9.9 ([7e78ca2](https://github.com/TheDataEngineX/dex/commit/7e78ca203347ff4c4000ca6ec42c335650da1b86))
- restructure release-please-config to packages format with last-release-sha ([46f0b69](https://github.com/TheDataEngineX/dex/commit/46f0b69b8372d54d26ba60eedd9095d7fb0f6cd3))
- sync dev to main ([40d5dff](https://github.com/TheDataEngineX/dex/commit/40d5dff99ae4295599badc848cd530df6eff9ffb))

### Documentation

- docs cleanup ([#211](https://github.com/TheDataEngineX/dex/issues/211)) ([0a6b7f7](https://github.com/TheDataEngineX/dex/commit/0a6b7f70287eb7399eb17acea2fb0ad09efd0597))

## [Unreleased]

## [1.0.0] - 2026-04-07

### Highlights

- **Complete Data + ML + AI Framework**: All phases from the v1.0 master plan implemented — config-driven pipeline via `dex.yaml`, BackendRegistry pattern for swappable backends, unified CLI.
- **Data Layer**: DuckDB connector (default), CSV connector, PipelineRunner with DAG resolution, transforms (filter, derive, cast, deduplicate), quality gates (completeness, uniqueness), column-level lineage tracking, built-in cron scheduler.
- **ML Layer**: SQLite-backed experiment tracker, DuckDB feature store, sklearn/xgboost training integration, model registry with versioning (dev → staging → production), built-in model serving via FastAPI, PSI drift detection.
- **AI Layer**: Built-in ReAct agent runtime, Ollama LLM provider (default), tool registry (sql_query, predict, search), BM25 sparse retrieval (DuckDB FTS), dense vector retrieval (DuckDB VSS HNSW), hybrid retrieval with RRF fusion, agent memory (short-term + episodic).
- **CLI Commands**: `dex init`, `dex validate`, `dex version`, `dex serve`, `dex run`, `dex train`, `dex agent`, `dex query`.
- **API**: FastAPI app factory, JWT auth, rate limiting, health endpoints, project CRUD, pipeline run/status, data explorer, ML experiments/models, agent chat/manage, WebSocket for live logs and streaming.
- **Backend Registry Pattern**: Every subsystem follows ABC + BackendRegistry[T] pattern with built-in implementations and optional extras (Dagster, MLflow, Qdrant, LanceDB, sentence-transformers, PySpark).

### Breaking Changes

- **FastAPI now optional**: Core install (`pip install dataenginex`) includes only lightweight deps. Install `[api]` extra for FastAPI/uvicorn: `pip install dataenginex[api]`
- **Cloud SDKs now optional**: Core install no longer requires boto3/google-cloud-storage/google-cloud-bigquery. Install `[cloud]` extra: `pip install dataenginex[cloud]`
- **Routers moved**: API routers moved to application packages. Use `from dataenginex.api import ...` directly (requires `[api]` extra)
- **Root `__init__.py` slimmed**: Re-exports removed. Import from submodules directly: `from dataenginex.api import HealthChecker` etc.

### Added

- **Full project templates**: `dex init --template [minimal|data-pipeline|ml-project|ai-agent|full-stack|career-intelligence]`
- **Docker support**: Multi-stage Dockerfile (`ghcr.io/thedataenginex/dex`), docker-compose.yml for full stack
- **SecOps**: PII scanning in pipelines, masking, audit trail
- **Quality schema**: Spark audit integration for data quality validation
- **Examples**: 5 runnable examples in `examples/` directory

### Verification checklist

1. `uv run poe lint` — Ruff checks clean
1. `uv run poe typecheck` — mypy strict (all modules)
1. `uv run poe test` — 663 passed, 36 skipped
1. `pip install dataenginex` — installs successfully
1. `dex validate dex.yaml` — validates config
1. `dex version` — shows version

## [0.7.1] - 2026-03-17

### Fixed

- **MLflow 3.x alias API** — `MLflowModelRegistry` now uses the alias-based API (`get_model_version_by_alias`, `set_registered_model_alias`, `delete_registered_model_alias`). MLflow 3.x removed all stage-based model management (`get_latest_versions`, `transition_model_version_stage`, `current_stage`).
- **Release workflow reliability** — removed `paths: - 'pyproject.toml'` filter from `release-dataenginex.yml`. GitHub suppresses all push-event workflow triggers when a commit modifies `.github/workflows/`; the tag-exists check inside the workflow handles no-ops.
- **Duplicate mypy override** — removed duplicate `[[tool.mypy.overrides]] module = ["mlflow.*"]` in `pyproject.toml` left by merge conflict.

### Changed

- **Cloud SDKs now optional** — `boto3`, `google-cloud-storage`, `google-cloud-bigquery` moved from core dependencies to `[project.optional-dependencies] cloud = [...]`. Install via `pip install dataenginex[cloud]`. Core install no longer requires any cloud SDK.
- **GCS emulator updated for 3.x** — `GCSStorage` now uses `ClientOptions(api_endpoint=...)` instead of the removed private `client._connection.API_BASE_URL`.
- **Dependency floors bumped** — pydantic 2.10, fastapi 0.135.1, pyarrow 23.0.1, sentence-transformers 5.3, mlflow 3.0, hatchling 1.29, mkdocstrings 1.0.

## [0.6.1] - 2026-03-15

### Added

- **`SentenceTransformerEmbedder`** — thin wrapper over `sentence-transformers` (`all-MiniLM-L6-v2` default). Install via `uv add 'dataenginex[ml]'`. Implements the `embed_fn` protocol for `RAGPipeline`.
- **`RAGPipeline.answer(question, llm, ...)`** — full retrieve → augment → generate loop in one call. Combines `build_context` with any `LLMProvider.generate_with_context`.
- **GitHub Actions upgraded to Node.js 24** — `ci.yml`, `pypi-publish.yml`, `release-dataenginex.yml`, `security.yml` now use `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v7`.
- **`examples/05_rag_demo.py`** — end-to-end RAG demo with `--embed`, `--llm`, `--model` CLI flags; Ollama fallback to MockProvider; uses `RAGPipeline.answer()`.

## [0.6.0] - 2026-03-03

### Changed — BREAKING

- **Routers removed** — `api/routers/v1.py` and `api/routers/ml.py` moved to application packages (e.g. `careerdex.api.routers`). `dataenginex` no longer ships any route definitions — it provides only reusable API utilities (auth, health, errors, pagination, rate limiting).
- **FastAPI is now optional** — Core install (`pip install dataenginex`) includes only lightweight deps: `pydantic`, `pyyaml`, `loguru`, `httpx`, `python-dotenv`, `prometheus-client`. API/middleware consumers must install `pip install dataenginex[api]` to get FastAPI, uvicorn, structlog, OpenTelemetry.
- **Root `__init__.py` slimmed** — `from dataenginex import ...` no longer re-exports `HealthChecker`, `HealthStatus`, `configure_logging`, `configure_tracing`, `get_logger`. Use `from dataenginex.api import ...` or `from dataenginex.middleware import ...` directly (requires `[api]` extra).
- **Domain extraction** — Removed all CareerDEX-specific code from the framework:
  - Removed domain schemas from `core/schemas.py`: `JobSourceEnum`, `JobLocation`, `JobBenefits`, `JobPosting`, `UserProfile`, `PipelineExecutionMetadata`, `DataQualityReport`
  - Removed domain validators from `core/validators.py`: `SchemaValidator`, `DataHash`, `QualityScorer`, domain-specific `DataQualityChecks` methods
  - Deleted `core/pipeline_config.py` (100% domain-specific)
  - Cleaned up all domain-specific docstring examples (`job_posting`, `job_classifier`, `salary_min`) → replaced with generic examples
- **Injectable `QualityGate`** — `QualityGate.__init__` now accepts `scorer`, `required_fields`, and `uniqueness_key` keyword arguments
- **Real `LocalParquetStorage`** — Reads/writes actual Parquet files via `pyarrow` (optional dep with `_HAS_PYARROW` guard)
- **`BigQueryStorage` stubbed** — All methods raise `NotImplementedError`

### Fixed

- **Pickle safety** — `ml/training.py` now uses `SafeUnpickler` restricting deserialization to sklearn/numpy namespaces only; HMAC signature verification on model load (`DATAENGINEX_MODEL_HMAC_KEY` env var)
- **Error swallowing** — `ml/training.py` `evaluate()` silence `except Exception: pass` → `except ImportError: logger.debug(...)` for optional metrics
- **LLM error handling** — `OllamaProvider.generate()`/`chat()` raise `ConnectionError` on HTTP failures instead of returning empty `LLMResponse`
- **Pagination cursor** — `decode_cursor()` raises `ValueError` on invalid input instead of silently returning 0
- **Storage backends** — `S3Storage.exists()` catches `NoSuchKey` specifically; `GCSStorage.exists()` returns `blob.exists()` directly with specific exception handling

### Added

- **RAG Vector DB adapter** — `VectorStoreBackend` ABC with `InMemoryBackend` and `ChromaDBBackend` implementations; `RAGPipeline` orchestrator for document ingestion and semantic retrieval; `Document` and `SearchResult` dataclasses (#94)
- **LLM integration** — `LLMProvider` ABC with `OllamaProvider` (local Ollama REST API) and `MockProvider` for testing; `generate_with_context()` for RAG-style augmented generation; `ChatMessage`, `LLMConfig`, `LLMResponse` dataclasses (#95)
- **CareerDEX Phase 1: Foundation** — config loading from `job_config.json`, schema validation (JobPosting, UserProfile, PipelineExecutionMetadata), medallion architecture bootstrap, sample data generation (#65)
- **CareerDEX Phase 2: Job Ingestion** — `JobSourceConnector` ABC with LinkedIn, Indeed, Glassdoor, CompanyCareerPages connectors; `DeduplicationEngine` for content-hash dedup; `JobIngestionPipeline` orchestrator (#66)
- **CareerDEX Phase 3: Feature Engineering** — `JobDescriptionParser` (skill/salary/seniority extraction), `ResumeParser`, `SkillNormalizer` with 30+ alias mappings and category taxonomy, `EmbeddingGenerator` with sentence-transformers + hash fallback, `InMemoryVectorStore` (#67)
- **CareerDEX Phase 4: ML Models** — `ResumeJobMatcher` (weighted cosine + skill/location/salary scoring), `SalaryPredictor` (XGBoost-style with location/seniority/skills adjustments), `SkillGapAnalyzer` (collaborative filtering), `CareerPathRecommender` (transition graph), `ChurnPredictor` (logistic regression) (#68)
- **CareerDEX Phase 5: API Services** — FastAPI router at `/api/v1/careerdex/` with endpoints: salary prediction, skill gap analysis, career paths, career health/churn risk, market trends, job recommendations; full Pydantic request/response models (#69)
- **CareerDEX Phase 6: Testing & Deployment** — `DeploymentConfig` with K8s manifest helpers, `MonitoringConfig` with 5 default Prometheus alert rules, `SecurityAudit` for secret scanning and SQL injection detection (#70)
- Re-exports in root `__init__.py` and `ml/__init__.py` for all new vector store and LLM symbols
- 82 new unit tests: `test_careerdex_phases.py` (55 tests), `test_vectorstore.py` (16 tests), `test_llm.py` (11 tests)

## [0.5.0] - 2026-03-01

### Added

- **Storage abstraction** — `list_objects(prefix)` and `exists(path)` on `StorageBackend` ABC; concrete implementations in `LocalParquetStorage`, `BigQueryStorage`, `JsonStorage`, `ParquetStorage`, `S3Storage`, `GCSStorage`; `get_storage(uri)` factory function (#89)
- **ML serving endpoints** — `POST /api/v1/predict`, `GET /api/v1/models`, `GET /api/v1/models/{name}` with `PredictRequestBody`/`PredictResponseBody` Pydantic models; ML-specific Prometheus metrics (`model_prediction_latency_seconds`, `model_prediction_total`, `model_predictions_in_flight`) (#92)
- **Drift monitoring scheduler** — `DriftScheduler` with background thread for periodic drift checks; `DriftMonitorConfig`, `DriftCheckResult` dataclasses; publishes PSI scores to `model_drift_psi` gauge; increments `model_drift_alerts_total` counter on drift detection (#93)
- Prometheus alert rules for drift monitoring — `ModelDriftModerate`, `ModelDriftSevere`, `DriftAlertSpike`, `DriftCheckStale` in `monitoring/alerts/drift_alerts.yml`
- `endpoint_url` parameter on `S3Storage` for LocalStack/emulator support
- `api_endpoint` parameter on `GCSStorage` for fake-gcs-server/emulator support
- Docker emulator stack (`docker-compose.test.yml`) — LocalStack 4.0 (S3) + fake-gcs-server 1.49 (GCS)
- 25 integration tests with emulator auto-detection in `tests/integration/test_storage_real.py`
- Terraform module for cloud test buckets (moved to infrastructure repo)
- Google-style docstrings across 55+ methods and 9 Pydantic models (#88)
- `py.typed` marker for PEP 561 compliance — downstream consumers get type checking support
- Module-level `__all__` in all 30 `.py` source files — every public symbol is explicitly gated
- Convenience re-exports in root `__init__.py` — `from dataenginex import MedallionArchitecture` etc.
- `core/__init__.py` now exports: `BigQueryStorage`, `DataLineage`, `DualStorage`, `LocalParquetStorage`, `StorageBackend`, `ComponentStatus`, `EchoRequest`, `EchoResponse`, `ReadinessResponse`, `StartupResponse`
- PyPI badge in README (#87)

### Fixed

- `docs-pages.yml` workflow: replaced `uv lock && uv sync` with `uv sync --frozen` to prevent lock drift in CI
- `Dockerfile` runtime stage: added missing `COPY --from=builder /build/packages /app/packages` for `PYTHONPATH` resolution
- mypy overrides for optional cloud SDKs (`boto3`, `google.auth`, `google.cloud`) — prevents `unused-ignore` vs `import-not-found` flip-flop depending on installed packages

## [0.4.11] - 2026-02-27

### Changed

- Added `environment` label support across HTTP metrics counters/histograms/gauges and middleware emission.
- Aligned alert rule histogram quantile expressions with explicit bucket aggregation by `le` and `environment`.
- Standardized docs and release prep metadata for CSV-canonical roadmap and setup workflow updates.

## [0.4.10] - 2026-02-21

### Added

- `examples/` directory with 4 runnable quickstart scripts
- `01_hello_pipeline.py` — profiler, schema validation, medallion config
- `02_api_quickstart.py` — FastAPI app with health, v1 router, metrics
- `03_quality_gate.py` — QualityGate evaluations against layer thresholds
- `04_ml_training.py` — SklearnTrainer, ModelRegistry, DriftDetector demo
- `examples/GUIDE.md` with table of examples and run instructions

## [0.4.8] - 2026-02-21

### Added

- PySpark local-mode test fixtures in `tests/conftest.py` (session-scoped `spark` session)
- Sample DataFrame fixtures: `spark_df_jobs`, `spark_df_weather`, `spark_df_empty`
- `requires_pyspark` skip marker — tests auto-skip when PySpark is not installed
- `tests/fixtures/sample_data.py` — factory helpers for job, user, and weather records
- `tests/unit/test_spark_fixtures.py` — validates PySpark fixture behaviour

## [0.4.6] - 2026-02-21

### Added

- `QualityGate` — orchestrates quality checks at medallion layer transitions
- `QualityStore` — in-memory store accumulating per-layer quality metrics
- `QualityResult` — immutable dataclass capturing evaluation outcomes
- `QualityDimension` — StrEnum for named quality dimensions
- `/api/v1/data/quality/{layer}` endpoint for per-layer quality history
- `set_quality_store()` / `get_quality_store()` for wiring quality at app startup
- New exports in `dataenginex.core` and `dataenginex.api`

### Changed

- `/api/v1/data/quality` now returns live metrics from `QualityStore` (was placeholder zeros)
- Wired `DataProfiler`, `DataQualityChecks`, and `QualityScorer` into `QualityGate` pipeline

## [0.4.5] - 2026-02-21

### Added

- `StorageBackend` ABC with proper `@abstractmethod` contracts
- `S3Storage` backend for AWS S3 (requires `boto3`)
- `GCSStorage` backend for Google Cloud Storage (requires `google-cloud-storage`)
- Re-exported `StorageBackend` from `dataenginex.lakehouse`

### Changed

- Refactored `StorageBackend` from plain class to proper `ABC` subclass
- Updated `lakehouse.__init__` to export all 4 storage backends + ABC

## [0.4.3] - 2026-02-21

### Added

- Comprehensive attribute-level docstrings on all public dataclasses
- `from __future__ import annotations` in all source modules
- Module-level class/function inventory docstrings
- mkdocs API reference configuration with `mkdocstrings` plugin
- API reference pages for all 7 subpackages under `docs/api-reference/`

### Changed

- Upgraded mkdocs theme from `mkdocs` to `material`
- Enhanced module docstrings in middleware, core, and validators

## [0.4.1] - 2026-02-21

### Added

- CHANGELOG.md with Keep a Changelog format
- Release workflow extracts changelog notes for GitHub Releases automatically

### Changed

- `release.yml` now reads `packages/dataenginex/CHANGELOG.md` for release notes

## [0.4.0] - 2026-02-21

### Added

- Stable `__all__` exports in every subpackage `__init__.py`
- `from __future__ import annotations` in all public modules
- Comprehensive module-level docstrings with usage examples
- New public API exports: `ComponentHealth`, `AuthMiddleware`, `AuthUser`,
  `create_token`, `decode_token`, `BadRequestError`, `NotFoundError`,
  `PaginationMeta`, `RateLimiter`, `RateLimitMiddleware`,
  `ConnectorStatus`, `FetchResult`, `ColumnProfile`, `get_logger`, `get_tracer`

### Changed

- Reorganized `__all__` in all subpackages for logical grouping
- Updated package version to 0.4.0

## [0.3.5] - 2026-02-13

### Added

- Production hardening: structured logging, Prometheus/OTel, health probes
- Data connectors: `RestConnector`, `FileConnector` with async interface
- Schema registry with versioned schema management
- Data profiler with automated dataset statistics
- Lakehouse catalog, partitioning, and storage backends
- ML framework: trainer, model registry, drift detection, serving
- Warehouse transforms and persistent lineage tracking
- JWT authentication middleware
- Rate limiting middleware
- Cursor-based pagination utilities
- Versioned API router (`/api/v1/`)

[0.3.5]: https://github.com/TheDataEngineX/DEX/releases/tag/v0.3.5
[0.4.0]: https://github.com/TheDataEngineX/DEX/compare/v0.3.5...v0.4.0
[0.4.1]: https://github.com/TheDataEngineX/DEX/compare/v0.4.0...v0.4.1
[0.4.10]: https://github.com/TheDataEngineX/DEX/compare/v0.4.8...v0.4.10
[0.4.11]: https://github.com/TheDataEngineX/DEX/compare/v0.4.10...v0.4.11
[0.4.3]: https://github.com/TheDataEngineX/DEX/compare/v0.4.1...v0.4.3
[0.4.5]: https://github.com/TheDataEngineX/DEX/compare/v0.4.3...v0.4.5
[0.4.6]: https://github.com/TheDataEngineX/DEX/compare/v0.4.5...v0.4.6
[0.4.8]: https://github.com/TheDataEngineX/DEX/compare/v0.4.6...v0.4.8
[0.5.0]: https://github.com/TheDataEngineX/DEX/compare/v0.4.11...v0.5.0
[1.0.0]: https://github.com/TheDataEngineX/DEX/releases/tag/v1.0.0
[unreleased]: https://github.com/TheDataEngineX/DEX/compare/v1.0.0...HEAD
