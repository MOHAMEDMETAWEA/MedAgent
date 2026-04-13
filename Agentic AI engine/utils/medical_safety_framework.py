"""
Medical Safety Framework - enforces regulatory guardrails and risk classification.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class MedicalSafetyFramework:
    EMERGENCY_KEYWORDS = [
        "chest pain",
        "shortness of breath",
        "severe bleeding",
        "unconscious",
        "stroke",
        "difficulty breathing",
        "heart attack",
        "poison",
        "overdose",
        "suicide",
        "hurt myself",
        "hopeless",
        "slurred speech",
        "numbness",
        "heavy bleeding",
        "fracture",
        "seizure",
        "allergic reaction",
    ]

    FORBIDDEN_TOPICS = [
        "dosage recommendation",
        "surgical instructions",
        "euthanasia",
        "illegal drug synthesis",
        "terminal advice without disclaimer",
    ]

    @staticmethod
    def classify_risk(symptoms: str) -> str:
        """Classifies the clinical risk level based on symptom severity."""
        symptoms_lower = symptoms.lower()

        # Emergency check
        if (
            any(
                kw in symptoms_lower for kw in MedicalSafetyFramework.EMERGENCY_KEYWORDS
            )
            or "hurt myself" in symptoms_lower
            or "hopeless" in symptoms_lower
        ):
            return "Emergency"

        # High Risk check (subjective, can be expanded)
        high_risk_triggers = ["pregnancy complications", "severe pain", "vision loss"]
        if any(tr in symptoms_lower for tr in high_risk_triggers):
            return "High"

        return "Medium" if len(symptoms_lower) > 50 else "Low"

    @staticmethod
    def get_mandatory_disclaimer(risk_level: str) -> str:
        """Returns the appropriate medical disclaimer based on risk."""
        if risk_level == "Emergency":
            return "⚠️ CRITICAL: This may be a medical emergency. Please seek immediate medical care or call 911/emergency services NOW."
        elif risk_level == "High":
            return "🚨 IMPORTANT: High-risk symptoms detected. This requires immediate professional evaluation."
        else:
            return "ℹ️ DISCLAIMER: This is an AI-generated suggestion and not a medical diagnosis. Consult a licensed physician."

    @staticmethod
    def validate_output(content: str, confidence: float) -> Tuple[bool, str]:
        """Ensures compliance with medical device AI best practices."""
        # Confidence Threshold
        if confidence < 0.5:
            return (
                False,
                "Confidence too low for clinical suggestion. Please consult a doctor.",
            )

        # Forbidden content filter
        content_lower = content.lower()
        for forbidden in MedicalSafetyFramework.FORBIDDEN_TOPICS:
            if forbidden in content_lower:
                return (
                    False,
                    f"Output contains restricted topic: {forbidden}. Please contact medical staff.",
                )

        return True, "Valid"
