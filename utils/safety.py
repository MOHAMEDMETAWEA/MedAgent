"""
Medical AI Safety Utilities
Provides strict input validation, injection protection, and medical safety checks.
"""

import logging
import re
from typing import List, Optional, Tuple

from config import settings
from utils.phi_redactor import phi_redactor

logger = logging.getLogger(__name__)

# Dangerous medical keywords that should trigger warnings/blocks
CRITICAL_KEYWORDS = [
    "suicide",
    "self-harm",
    "overdose",
    "poison",
    "cardiac arrest",
    "stroke",
    "severe",
    "critical",
    "emergency",
    "immediate",
    "urgent",
    "kill",
    "die",
    "death",
    "chest pain",
    "shortness of breath",
    "difficulty breathing",
]

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions?",
    r"forget\s+(previous|all|above)\s+instructions?",
    r"disregard\s+(previous|all|above)",
    r"^\s*system\s*:\s*",
    r"^\s*assistant\s*:\s*",
    r"<\|[a-z_]+\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"developer\s+mode",
    r"uncensored",
]


def detect_prompt_injection(text: str) -> bool:
    """Detects common LLM adversarial patterns."""
    injection_patterns = [
        r"ignore (all )?previous instructions",
        r"system prompt",
        r"new role",
        r"act as",
        r"you are now",
        r"DAN mode",
        r"jailbreak",
        r"disregard (all )?safety",
        r"speak in",
        r"from now on",
    ]
    combined = "|".join(injection_patterns)
    if re.search(combined, text, re.IGNORECASE):
        logger.critical(
            f"SECURITY: Potential Prompt Injection Detected: '{text[:100]}...'"
        )
        return True
    return False


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent injection attacks and ensure safety.
    Now includes automatic PHI redaction.
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Check for injection first
    if detect_prompt_injection(text):
        return "ERROR: Malicious input detected. Request blocked by Safety Layer."

    # 2. PHI Redaction (Cycle 5 Security Requirement)
    text = phi_redactor.redact(text)

    # 3. Control Character Cleanup
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", text)

    # 4. Length Enforcement
    max_len = max_length or settings.MAX_INPUT_LENGTH
    if len(text) > max_len:
        text = text[:max_len]
        logger.warning(f"Input truncated: {len(text)} > {max_len}")

    # 4. Whitespace Normalization
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _detect_injection_patterns(text: str) -> Tuple[bool, List[str]]:
    """
    Legacy pattern-based injection detection (Tuple return).
    Internal use only — primary API is detect_prompt_injection().
    """
    detected = []

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            detected.append(pattern)

    return len(detected) > 0, detected


def detect_critical_symptoms(text: str) -> Tuple[bool, List[str]]:
    """
    Detect critical/emergency keywords in symptoms.
    """
    detected = []
    text_lower = text.lower()

    for keyword in CRITICAL_KEYWORDS:
        # Simple keyword matching - could be improved with NLP
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
            detected.append(keyword)

    return len(detected) > 0, detected


def validate_medical_input(text: str) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive validation of medical input.
    """
    if not text or len(text.strip()) == 0:
        return False, "Input cannot be empty"

    if len(text) > settings.MAX_INPUT_LENGTH:
        return False, f"Input exceeds maximum length of {settings.MAX_INPUT_LENGTH}"

    # Check for prompt injection
    is_injection, patterns = _detect_injection_patterns(text)
    if is_injection:
        logger.warning(f"Blocked input due to injection patterns: {patterns}")
        return False, "Unsafe input detected"

    # Basic gibberish check (example: >50% non-alphanumeric and not punctuation)
    # alpha_ratio = sum(c.isalnum() for c in text) / len(text)
    # if alpha_ratio < 0.3:
    #     return False, "Input appears to be malformed"

    return True, None


def add_safety_disclaimer(response: str) -> str:
    """
    Add medical safety disclaimer to AI responses.
    """
    disclaimer = (
        "\n\n---\n"
        "⚠️ **IMPORTANT MEDICAL DISCLAIMER**:\n"
        "This system is for educational and informational purposes only. "
        "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
        "Always seek the advice of qualified healthcare providers. "
        "In case of a medical emergency, contact your local emergency services immediately.\n"
        "---\n"
    )
    # Avoid double disclaimer
    if "IMPORTANT MEDICAL DISCLAIMER" in response:
        return response
    return response + disclaimer
