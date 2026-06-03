"""PII detection — identify personally-identifiable information in records.

Uses regex patterns to detect common PII types by field name and value.
No ML model required; runs in-process with zero external dependencies.

Supported PII types
-------------------
EMAIL, PHONE, SSN, CREDIT_CARD, IP_ADDRESS, DATE_OF_BIRTH, NAME, ADDRESS
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

__all__ = [
    "PIIDetector",
    "PIIField",
    "PIIType",
    "TextMatch",
]


class PIIType(StrEnum):
    """Categories of personally-identifiable information."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    NAME = "name"
    ADDRESS = "address"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PIIField:
    """A detected PII field in a record.

    Attributes:
        field_name: Name of the record key containing PII.
        pii_type: Detected PII category.
        confidence: Detection confidence 0.0–1.0.
        sample: Masked sample value (last 4 chars only) for audit purposes.
    """

    field_name: str
    pii_type: PIIType
    confidence: float
    sample: str = ""


@dataclass(frozen=True)
class TextMatch:
    """A PII match found in a span of free-form text.

    Used by ``PIIDetector.scan_text`` and ``MaskingEngine.mask_text`` for
    prompt-level scanning (the call-level path used by ``PrivacyGuard``).

    Attributes:
        pii_type: Detected PII category.
        value: The matched substring (kept verbatim for masking).
        start: Inclusive start index into the source text.
        end: Exclusive end index into the source text.
        confidence: Detection confidence 0.0–1.0.
    """

    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 0.0


# Name-based hints: if the field name contains any of these tokens,
# we assign a high-confidence match for the mapped PIIType.
_NAME_HINTS: dict[str, PIIType] = {
    "email": PIIType.EMAIL,
    "mail": PIIType.EMAIL,
    "phone": PIIType.PHONE,
    "mobile": PIIType.PHONE,
    "cell": PIIType.PHONE,
    "ssn": PIIType.SSN,
    "social": PIIType.SSN,
    "tax_id": PIIType.SSN,
    "national_id": PIIType.SSN,
    "credit_card": PIIType.CREDIT_CARD,
    "card_number": PIIType.CREDIT_CARD,
    "pan": PIIType.CREDIT_CARD,
    "ip": PIIType.IP_ADDRESS,
    "ip_address": PIIType.IP_ADDRESS,
    "dob": PIIType.DATE_OF_BIRTH,
    "birth": PIIType.DATE_OF_BIRTH,
    "birthdate": PIIType.DATE_OF_BIRTH,
    "birthday": PIIType.DATE_OF_BIRTH,
    "first_name": PIIType.NAME,
    "last_name": PIIType.NAME,
    "full_name": PIIType.NAME,
    "surname": PIIType.NAME,
    "given_name": PIIType.NAME,
    "address": PIIType.ADDRESS,
    "street": PIIType.ADDRESS,
    "postcode": PIIType.ADDRESS,
    "zip_code": PIIType.ADDRESS,
    "zipcode": PIIType.ADDRESS,
    "postal": PIIType.ADDRESS,
}

# Value-based regex patterns (compiled once at import time)
_VALUE_PATTERNS: list[tuple[PIIType, re.Pattern[str], float]] = [
    (PIIType.EMAIL, re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), 0.95),
    (PIIType.SSN, re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"), 0.90),
    (
        PIIType.CREDIT_CARD,
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        0.85,
    ),
    (
        PIIType.PHONE,
        re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        0.80,
    ),
    (PIIType.IP_ADDRESS, re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), 0.90),
    (
        PIIType.DATE_OF_BIRTH,
        re.compile(r"\b(?:\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b"),
        0.60,
    ),
]


class PIIDetector:
    """Detect PII fields in records using name hints and value patterns.

    Parameters
    ----------
    confidence_threshold:
        Minimum confidence to report a field as PII (default: 0.5).
    """

    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self._threshold = confidence_threshold

    def scan_record(self, record: dict[str, Any]) -> list[PIIField]:
        """Return all PII fields detected in a single record."""
        findings: list[PIIField] = []
        for field_name, value in record.items():
            field = self._check_field(field_name, value)
            if field is not None:
                findings.append(field)
        return findings

    def scan_dataset(self, records: list[dict[str, Any]]) -> dict[str, PIIField]:
        """Scan a list of records and return the unique PII fields found.

        Returns a dict keyed by field name (deduped across records).
        """
        detected: dict[str, PIIField] = {}
        for record in records:
            for finding in self.scan_record(record):
                if finding.field_name not in detected:
                    detected[finding.field_name] = finding
        return detected

    def pii_field_names(self, records: list[dict[str, Any]]) -> set[str]:
        """Return just the field names that contain PII."""
        return set(self.scan_dataset(records).keys())

    def scan_text(self, text: str) -> list[TextMatch]:
        """Find all PII spans in a free-form string.

        Runs every value-based regex pattern that meets the configured
        confidence threshold over *text* and returns matches sorted by
        start position. Overlapping spans from different patterns are
        deduplicated, keeping the leftmost / highest-confidence match.

        This is the scanner used by :class:`PrivacyGuard` for outbound
        LLM prompts.
        """
        if not text:
            return []
        matches: list[TextMatch] = []
        for pii_type, pattern, confidence in _VALUE_PATTERNS:
            if confidence < self._threshold:
                continue
            for m in pattern.finditer(text):
                matches.append(
                    TextMatch(
                        pii_type=pii_type,
                        value=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=confidence,
                    )
                )
        return _dedupe_overlapping(matches)

    def _check_field(self, field_name: str, value: Any) -> PIIField | None:
        """Check a single field by name then by value pattern."""
        lower_name = field_name.lower()

        # Name-hint check (high confidence)
        for hint, pii_type in _NAME_HINTS.items():
            if hint in lower_name:
                sample = _safe_sample(value)
                if self._threshold <= 0.85:
                    return PIIField(
                        field_name=field_name,
                        pii_type=pii_type,
                        confidence=0.85,
                        sample=sample,
                    )

        # Value-pattern check
        str_value = str(value) if value is not None else ""
        for pii_type, pattern, confidence in _VALUE_PATTERNS:
            if confidence >= self._threshold and pattern.search(str_value):
                return PIIField(
                    field_name=field_name,
                    pii_type=pii_type,
                    confidence=confidence,
                    sample=_safe_sample(value),
                )

        return None


def _safe_sample(value: Any, keep_last: int = 4) -> str:
    """Return the last *keep_last* characters for audit reference only."""
    s = str(value) if value is not None else ""
    if len(s) <= keep_last:
        return "*" * len(s)
    return "*" * (len(s) - keep_last) + s[-keep_last:]


def _dedupe_overlapping(matches: list[TextMatch]) -> list[TextMatch]:
    """Sort *matches* by start; drop any that overlap an earlier kept match.

    When two patterns hit the same span (e.g. credit card and phone), the
    higher-confidence one is preferred. Stable for equal confidence —
    earlier-detected wins.
    """
    if not matches:
        return []
    # Sort by start, then by confidence desc so highest confidence wins for ties
    sorted_matches = sorted(matches, key=lambda m: (m.start, -m.confidence))
    kept: list[TextMatch] = []
    for m in sorted_matches:
        if kept and m.start < kept[-1].end:
            # Overlaps the previously kept span — skip unless strictly higher confidence
            if m.confidence > kept[-1].confidence:
                kept[-1] = m
            continue
        kept.append(m)
    return kept
