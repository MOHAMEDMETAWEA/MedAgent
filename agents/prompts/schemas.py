"""
Schemas for MedAgent Prompt Ecosystem.
Ensures every prompt output follows a strict, audit-safe structure.
"""
from typing import Dict, Any

DIAGNOSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string", "description": "The primary clinical impression or differential diagnosis."},
        "reasoning": {"type": "string", "description": "The step-by-step logic used to arrive at the diagnosis."},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
        "differential_diagnoses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of other potential conditions considered."
        },
        "risk_stratification": {
            "type": "string",
            "enum": ["low", "medium", "high", "emergency"],
            "description": "The assessed risk level of the patient's condition."
        },
        "escalation_required": {"type": "boolean"},
        "suggested_next_steps": {"type": "array", "items": {"type": "string"}},
        "uncertainty_disclosure": {"type": "string", "description": "Mandatory disclosure of what remains uncertain."}
    },
    "required": ["diagnosis", "reasoning", "confidence_score", "risk_stratification", "uncertainty_disclosure"]
}

TRIAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "priority_level": {"type": "integer", "minimum": 1, "maximum": 5, "description": "ESI (Emergency Severity Index) level."},
        "justification": {"type": "string"},
        "immediate_actions": {"type": "array", "items": {"type": "string"}},
        "is_emergency": {"type": "boolean"}
    },
    "required": ["priority_level", "justification", "is_emergency"]
}

IMAGE_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {"type": "string", "description": "Detailed description of anomalies or features found in the image."},
        "anatomical_location": {"type": "string"},
        "abnormality_detected": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "recommended_specialist": {"type": "string"}
    },
    "required": ["findings", "abnormality_detected", "confidence"]
}

SAFETY_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "safe_to_release": {"type": "boolean"},
        "violation_types": {"type": "array", "items": {"type": "string"}},
        "redacted_content": {"type": "string", "description": "The response with PII or unsafe medical advice removed."},
        "explanation": {"type": "string"}
    },
    "required": ["safe_to_release", "violation_types"]
}

# Mapping of prompt types to schemas
SCHEMAS = {
    "diagnosis": DIAGNOSIS_SCHEMA,
    "triage": TRIAGE_SCHEMA,
    "vision": IMAGE_ANALYSIS_SCHEMA,
    "safety": SAFETY_AUDIT_SCHEMA
}
