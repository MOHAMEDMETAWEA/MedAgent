"""
Medical AI Safety Utilities
Provides strict input validation, injection protection, and medical safety checks.
"""
import re
from typing import List, Tuple, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

# Dangerous medical keywords that should trigger warnings/blocks
CRITICAL_KEYWORDS = [
    "suicide", "self-harm", "overdose", "poison", 
    "cardiac arrest", "stroke", "severe", "critical",
    "emergency", "immediate", "urgent", "kill", "die", "death"
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

def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input to prevent injection attacks and ensure safety.
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)
    
    # Limit length
    max_len = max_length or settings.MAX_INPUT_LENGTH
    if len(text) > max_len:
        text = text[:max_len]
        logger.warning(f"Input truncated due to length violation: {len(text)} > {max_len}")
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """
    Detect potential prompt injection attacks.
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
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
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
    is_injection, patterns = detect_prompt_injection(text)
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
