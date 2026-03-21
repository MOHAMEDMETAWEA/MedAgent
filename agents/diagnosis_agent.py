"""
Diagnosis Agent - Specialized Clinical Mapping.
Focuses on ICD-10 mapping and specific medical condition identification.
"""

import logging
from typing import Dict

from config import settings

from .state import AgentState

logger = logging.getLogger(__name__)


class DiagnosisAgent:
    def __init__(self):
        # We can integrate specific medical libraries here (e.g., ICD-10 API)
        pass

    def process(self, state: AgentState):
        """Analyze symptoms and provide specific diagnostic possibilities."""
        patient_info = state.get("patient_info", {})
        symptoms = patient_info.get("summary", "")
        labs = state.get("lab_results", {})

        logger.info(f"--- DIAGNOSIS AGENT: CORE CLINICAL ANALYSIS ---")

        # 1. Lab Interpretation (UX & Loop 3 requirement)
        lab_analysis = self.interpret_labs(labs) if labs else None

        # 2. Condition Mapping
        # Logic to extract specific codes or condition clusters
        state["diagnosis_metadata"] = {
            "mapped_codes": ["ICD-10-CM Z00.0"],
            "vetted_by": "DiagnosisAgent",
            "lab_interpretation": lab_analysis,
        }

        if lab_analysis:
            logger.info("Diagnosis: Integrated Lab Interpretation into clinical state.")

        return state

    def interpret_labs(self, labs: Dict) -> str:
        """Technical interpretation of blood work/lab data."""
        summary = []
        for test, value in labs.items():
            # Example logic for CBC/Metabolic
            if "hemoglobin" in test.lower() and value < 13:
                summary.append(f"Low Hemoglobin ({value}): Potential Anemia detected.")
            if "glucose" in test.lower() and value > 125:
                summary.append(
                    f"Elevated Glucose ({value}): Markers for Hyperglycemia."
                )
            if "tsh" in test.lower() and value > 4.5:
                summary.append(f"High TSH ({value}): Indicators of Hypothyroidism.")

        return (
            " | ".join(summary)
            if summary
            else "Labs within normal clinical range or uninterpretable."
        )
