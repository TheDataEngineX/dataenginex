# Decision log

## 0014 - Cloud platform + cost (ADR-012, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: published comparisons put a small production PaaS stack at
about $54-82/month (Fly.io's PaaS pricing comparison, Oct 2026) and
S3 storage at $0.023/GB-month. The study's all-in estimate for
single-digit tenants is roughly $75-250/month - an estimate built
from those published rows, not a quote.

Decision: PaaS-class hosting plus S3-API storage, with a monthly
infrastructure budget cap and an alert.

Consequences: a solo founder needs the bill to be boring. The cap
is configured before the first cloud tenant, not after the first
surprise.
