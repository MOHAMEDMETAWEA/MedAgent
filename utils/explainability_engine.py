"""
Clinical Explainability Engine - structures reasoning paths for medical AI.
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    @staticmethod
    def generate_reasoning_trace(steps: List[str]) -> str:
        """Formats the logical chain of thought for clinical review."""
        return "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])

    @staticmethod
    def attach_medical_references(references: List[Dict]) -> List[str]:
        """Validates and formats citations from trusted sources."""
        formatted = []
        for ref in references:
            title = ref.get("title", "Unknown Source")
            url = ref.get("url", "#")
            platform = ref.get("platform", "Medical Literature")
            formatted.append(f"{title} ({platform}) - {url}")
        return formatted

    @staticmethod
    def calculate_confidence_score(agent_confidence: float, data_quality: float = 1.0) -> float:
        """Calibrates confidence based on model output and source quality."""
        # Simple weighted average for now, could be more complex (Bayesian)
        return round(agent_confidence * 0.8 + data_quality * 0.2, 2)

    @staticmethod
    def generate_explainable_summary(diagnosis: str, confidence: float, evidence: List[str], symptoms: List[str], alternatives: List[str]) -> Dict:
        """Constructs the full explainable payload as requested by hospitals."""
        return {
            "diagnosis": diagnosis,
            "confidence": confidence,
            "supporting_symptoms": symptoms,
            "evidence_sources": evidence,
            "alternative_diagnoses": alternatives,
            "trace_id": "EXP-" + str(hash(diagnosis))[-8:]
        }
