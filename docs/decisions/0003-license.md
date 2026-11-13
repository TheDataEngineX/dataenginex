# Decision log

## 0003 - License: Apache-2.0 + DCO (ADR-001, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: the fresh start removed the MIT continuity argument. The
research is blunt: Apache-2.0 is the standard for shared cores, an
MIT-licensed library is excluded from other products' cores, and
relicense backlash is fast and documented (HashiCorp to OpenTofu in
about 40 days).

Decision: the foundation is licensed Apache-2.0 with DCO sign-off
(no CLA). A separate trademark policy and a public no-relicense
pledge for the foundation accompany the license.

Consequences: LICENSE and CONTRIBUTING updated in this repo. The
trademark policy and the pledge live in the org .github repo. This
supersedes the MIT line in decision 0001.
