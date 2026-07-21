# dataenginex.secops

Security operations — PII detection, data masking, audit logging, and a combined scan+mask+audit gate.

## Quick import

```python
from dataenginex.secops import (
    PIIDetector,
    MaskingEngine,
    MaskingStrategy,
    AuditLogger,
    SecOpsGate,
    PrivacyGuard,
)
```

______________________________________________________________________

## PII Detection

`dataenginex.secops.pii`

Detects PII in records using field-name hints and value-pattern regexes (email, phone, SSN, credit card, IP address, date-of-birth).

::: dataenginex.secops.pii

**Key class:** `PIIDetector`

```python
from dataenginex.secops.pii import PIIDetector

detector = PIIDetector(confidence_threshold=0.5)
detected = detector.scan_dataset(records)  # dict[field_name, PIIField]
for field_name, finding in detected.items():
    print(field_name, finding.pii_type, finding.confidence)
```

______________________________________________________________________

## Data Masking

`dataenginex.secops.masking`

Masks PII fields in records. Supports redact, hash, partial (keep last N chars), and tokenize strategies.

::: dataenginex.secops.masking

**Key class:** `MaskingEngine`

```python
from dataenginex.secops.masking import MaskingEngine, MaskingStrategy

masker = MaskingEngine(
    default_strategy=MaskingStrategy.REDACT,
    field_strategies={"email": MaskingStrategy.HASH, "phone": MaskingStrategy.PARTIAL},
)
masked_records = masker.mask_dataset(records, pii_fields={"email", "phone"})
```

______________________________________________________________________

## Audit Logging

`dataenginex.secops.audit`

Structured audit log for PII scan/mask operations. Persisted to SQLite (WAL mode) — in-memory by default, file-backed when a `db_path` is given.

::: dataenginex.secops.audit

**Key class:** `AuditLogger`

```python
from dataenginex.secops.audit import AuditLogger

audit = AuditLogger(db_path=".dex/audit.db")
audit.log_scan(
    dataset_name="ingest_events",
    pii_fields=["email"],
    record_count=1250,
    actor="svc-account",
)
recent = audit.events_for("ingest_events")
```

______________________________________________________________________

## SecOps Gate

`dataenginex.secops.gate`

Scans a batch of records for PII, masks the detected fields, and emits an audit event for both steps — in one call. Combines `PIIDetector`, `MaskingEngine`, and `AuditLogger`.

::: dataenginex.secops.gate

**Key class:** `SecOpsGate`

```python
from dataenginex.secops import SecOpsGate, MaskingStrategy

gate = SecOpsGate(
    field_strategies={"email": MaskingStrategy.HASH},
    dataset_name="users",
)
clean_records = gate.process(raw_records)
```

______________________________________________________________________

## Privacy Guard

`dataenginex.secops.guard`

Pre-send PII interception for outbound LLM calls: scans a prompt, then masks or blocks it before it leaves the process. Compose with a provider via `dataenginex.ai.routing.guarded.GuardedProvider`, or call `process()` directly.

::: dataenginex.secops.guard

**Key class:** `PrivacyGuard`

```python
from dataenginex.secops.guard import PrivacyGuard

guard = PrivacyGuard()
result = guard.process("Contact me at jane@example.com", target="openai")
print(result.safe_prompt)   # PII masked unless target is a local provider
print(result.detections)    # tuple of TextMatch hits
```
