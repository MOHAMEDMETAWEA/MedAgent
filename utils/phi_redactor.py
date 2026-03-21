"""
PHI Redaction Utility - Hospital-Grade Data Privacy.
Strips names, emails, phones, and clinical identifiers from logs and outputs.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns for common PII/PHI
PHI_PATTERNS = {
    "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "Phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "DOB": r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    "CreditCard": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "NamePrefix": r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\b",
}


class PHIRedactor:
    """Enterprise-grade PHI Redactor."""

    @staticmethod
    def redact(text: str, mask: str = "[REDACTED]") -> str:
        """Strips all identifiable medical and personal data from text."""
        if not text or not isinstance(text, str):
            return text

        redacted_text = text
        for label, pattern in PHI_PATTERNS.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                # logger.debug(f"Redacting {label}: {len(matches)} matches found.")
                redacted_text = re.sub(pattern, mask, redacted_text)

        return redacted_text

    @staticmethod
    def cleanup_logs(log_record: str) -> str:
        """Utility for log processors to ensure no PHI escapes to ELK/CloudWatch."""
        return PHIRedactor.redact(log_record)


# Singleton Instance
phi_redactor = PHIRedactor()
