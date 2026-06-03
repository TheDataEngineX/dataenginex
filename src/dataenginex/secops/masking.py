"""PII masking — apply masking strategies to sensitive fields in records.

Strategies
----------
REDACT      Replace the value with a fixed string (``"[REDACTED]"``).
HASH        Replace with a SHA-256 hex digest (deterministic, irreversible).
PARTIAL     Keep the last N characters, mask the rest with ``*``.
TOKENIZE    Replace with a deterministic opaque token (``"tok_<sha8>..."``).
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import TYPE_CHECKING, Any, assert_never

if TYPE_CHECKING:
    from dataenginex.secops.pii import PIIType, TextMatch

__all__ = [
    "MaskingEngine",
    "MaskingStrategy",
]

_REDACT_VALUE = "[REDACTED]"
_HASH_SALT = "dex-secops-v1"  # salt prefix — change per environment via env var


class MaskingStrategy(StrEnum):
    """How to mask a PII field value."""

    REDACT = "redact"
    HASH = "hash"
    PARTIAL = "partial"
    TOKENIZE = "tokenize"


class MaskingEngine:
    """Apply masking strategies to PII fields in records.

    Parameters
    ----------
    default_strategy:
        Strategy used when a field has no explicit override.
    field_strategies:
        Per-field overrides: ``{"email": MaskingStrategy.HASH}``.
    partial_keep_last:
        Number of trailing characters to expose for ``PARTIAL`` masking.
    salt:
        Salt prefix for hash/tokenize operations.  Override per environment.
    """

    def __init__(
        self,
        default_strategy: MaskingStrategy = MaskingStrategy.REDACT,
        field_strategies: dict[str, MaskingStrategy] | None = None,
        *,
        partial_keep_last: int = 4,
        salt: str = _HASH_SALT,
    ) -> None:
        self._default = default_strategy
        self._field_strategies = field_strategies or {}
        self._keep_last = partial_keep_last
        self._salt = salt

    def mask_record(
        self,
        record: dict[str, Any],
        pii_fields: set[str],
    ) -> dict[str, Any]:
        """Return a copy of *record* with all *pii_fields* masked.

        Non-PII fields are passed through unchanged.
        """
        result = {}
        for key, value in record.items():
            if key in pii_fields:
                strategy = self._field_strategies.get(key, self._default)
                result[key] = self._apply(value, strategy)
            else:
                result[key] = value
        return result

    def mask_dataset(
        self,
        records: list[dict[str, Any]],
        pii_fields: set[str],
    ) -> list[dict[str, Any]]:
        """Return a masked copy of every record in *records*."""
        return [self.mask_record(r, pii_fields) for r in records]

    def mask_text(
        self,
        text: str,
        matches: list[TextMatch],
        strategies: dict[PIIType, MaskingStrategy] | None = None,
    ) -> str:
        """Return *text* with every match in *matches* replaced.

        Used by :class:`~dataenginex.secops.guard.PrivacyGuard` to redact PII
        from outbound LLM prompts. ``strategies`` maps each :class:`PIIType`
        to its masking strategy; PII types absent from the map fall back to
        ``self._default``.

        Replacements are applied from right to left so earlier indices stay
        valid as the string shrinks/grows.
        """
        if not matches:
            return text
        strategy_map = strategies or {}
        # Apply replacements right-to-left to preserve indices
        ordered = sorted(matches, key=lambda m: m.start, reverse=True)
        result = text
        for match in ordered:
            strategy = strategy_map.get(match.pii_type, self._default)
            replacement = self._apply(match.value, strategy)
            result = result[: match.start] + replacement + result[match.end :]
        return result

    def _apply(self, value: Any, strategy: MaskingStrategy) -> str:
        """Apply a single masking strategy to *value*."""
        if value is None:
            return _REDACT_VALUE

        str_value = str(value)

        if strategy == MaskingStrategy.REDACT:
            return _REDACT_VALUE

        if strategy == MaskingStrategy.HASH:
            return self._sha256(str_value)

        if strategy == MaskingStrategy.PARTIAL:
            n = self._keep_last
            if len(str_value) <= n:
                return "*" * len(str_value)
            return "*" * (len(str_value) - n) + str_value[-n:]

        if strategy == MaskingStrategy.TOKENIZE:
            digest = self._sha256(str_value)
            return f"tok_{digest[:16]}"

        assert_never(strategy)

    def _sha256(self, value: str) -> str:
        """Return a SHA-256 hex digest of the salted value."""
        payload = f"{self._salt}:{value}".encode()
        return hashlib.sha256(payload).hexdigest()
