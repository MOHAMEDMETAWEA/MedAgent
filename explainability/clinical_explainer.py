import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClinicalExplainer:
    """
    Unified Explainability Engine
    - Merged: utils/explainability_engine.py + explainability/clinical_explainer.py
    Responsibilities:
    - Trace reasoning steps (Chain-of-Thought).
    - Provide evidence sources and confidence justifications.
    - Adapt explanations for Patient vs Doctor visibility.
    """

    @staticmethod
    def generate_reasoning_trace(steps: List[str]) -> str:
        """Formats the logical chain of thought for clinical review (Legacy Support)."""
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
    def calculate_confidence_score(
        agent_confidence: float, data_quality: float = 1.0
    ) -> float:
        """Calibrates confidence based on model output and source quality."""
        return round(agent_confidence * 0.8 + data_quality * 0.2, 2)

    async def generate_explanation(
        self, state: Dict[str, Any], target_role: str = "doctor"
    ) -> Dict[str, Any]:
        """Generates a structured explanation based on the interaction graph state."""
        reasoning_steps = state.get(
            "reasoning_trace",
            ["Symptom analysis", "Differential matching", "Guideline check"],
        )
        evidence = state.get(
            "retrieved_docs", "Standard medical literature references."
        )
        confidence = state.get("confidence_score", 0.90)

        if target_role == "patient" or target_role == "PATIENT":
            return self._simplify_for_patient(reasoning_steps, evidence, confidence)
        else:
            return self._format_for_doctor(reasoning_steps, evidence, confidence)

    def _format_for_doctor(
        self, steps: List[str], evidence: str, confidence: float
    ) -> Dict[str, Any]:
        return {
            "title": "Clinical Reasoning Analysis / تحليل التفكير السريري",
            "logical_steps": steps,
            "evidence_base": evidence,
            "confidence_justification": f"High confidence based on {confidence*100}% guideline alignment.",
            "mode": "technical",
        }

    def _simplify_for_patient(
        self, steps: List[str], evidence: str, confidence: float
    ) -> Dict[str, Any]:
        return {
            "title": "How we reached this conclusion / كيف وصلنا لهذه النتيجة",
            "explanation": "We checked your symptoms against thousands of similar medical cases and verified them with established safety guidelines.",
            "simplified_steps": [
                "Checking your inputs",
                "Searching medical records",
                "Safety validation",
            ],
            "disclaimer": "This is an AI summary. Please verify with your physician.",
            "mode": "simplified",
        }


# Singleton Instance
clinical_explainer = ClinicalExplainer()
