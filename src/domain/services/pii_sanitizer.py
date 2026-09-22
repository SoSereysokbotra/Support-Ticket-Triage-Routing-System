"""
PII Sanitization Domain Service.
Detects and masks sensitive Personally Identifiable Information (PII)
prior to processing by generative Copilot language models or external APIs.
"""

from __future__ import annotations

import re
from typing import Dict, Tuple


class PIISanitizer:
    """
    High-performance regex masking engine for sensitive customer telemetry.
    Ensures compliance with GDPR, PCI-DSS, and HIPAA guidelines.
    """

    PATTERNS: Dict[str, Tuple[re.Pattern, str]] = {
        "CREDIT_CARD": (
            re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
            "[REDACTED_CARD]",
        ),
        "SSN": (
            re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "[REDACTED_SSN]",
        ),
        "API_KEY": (
            re.compile(
                r"\b(?:sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_\-\.]{20,})\b",
                re.IGNORECASE,
            ),
            "[REDACTED_API_KEY]",
        ),
        "EMAIL": (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "[REDACTED_EMAIL]",
        ),
        "PHONE": (
            re.compile(r"\b(?:\+?1[-. ]?)?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b"),
            "[REDACTED_PHONE]",
        ),
    }

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Masks all identified PII entities in the input text.
        Returns:
            sanitized_text: String with PII replaced by entity tokens.
            redaction_counts: Map of entity types to number of redacts performed.
        """
        if not text:
            return "", {}

        sanitized = text
        counts: Dict[str, int] = {}

        for entity_type, (pattern, replacement) in cls.PATTERNS.items():
            matches = pattern.findall(sanitized)
            if matches:
                counts[entity_type] = len(matches)
                sanitized = pattern.sub(replacement, sanitized)

        return sanitized, counts

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Quick boolean scan to determine if text contains any PII entities."""
        if not text:
            return False
        return any(pattern.search(text) is not None for pattern, _ in cls.PATTERNS.values())
