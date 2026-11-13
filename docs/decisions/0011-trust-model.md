# Decision log

## 0011 - Trust model (ADR-009, design study) (2026-11-12)

Status: accepted (design study default, approved by Jay 2026-11-12).

Context: the research is blunt - RestrictedPython explicitly is not
a sandbox, and no safe in-process Python sandbox exists.

Decision: locally, user definitions are trusted code (the user's
own machine, the user's own files). In cloud, one ephemeral,
egress-restricted container per tenant job IS the sandbox.

Consequences: cloud jobs run the identical image as local jobs
(decision 0018). Egress allow-listing is a cloud-layer build item,
not a Layer 0 concern.
