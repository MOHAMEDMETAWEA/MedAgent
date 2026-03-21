"""
SOAP Agent - The Clinical Scribe.
Automates the generation of SOAP notes (Subjective, Objective, Assessment, Plan) for doctors.
"""

import logging
from typing import Any, Dict

from langchain.prompts import ChatPromptTemplate

from models.model_router import get_model

logger = logging.getLogger(__name__)


class SoapAgent:
    def __init__(self):
        self.llm = get_model()
        self.system_prompt = """
        You are a highly efficient Medical Scribe.
        Transform the clinical interaction trace into a professional SOAP Note.
        
        FORMAT:
        1. **Subjective (S)**: Patient's symptoms, history, and concerns in their own words.
        2. **Objective (O)**: Vital signs, imaging results, and physical findings from EHR/Vision.
        3. **Assessment (A)**: Clinical impression, differential diagnoses, and risk assessment.
        4. **Plan (P)**: Recommended medications, tests, referrals, and follow-up.

        RULES:
        - Use technical medical terminology.
        - Be concise and structured.
        - Include ICPC-2/ICD-10 codes if possible from the diagnosis.
        """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured SOAP documentation."""
        symptoms = (
            state.get("messages", [None])[-1].content
            if state.get("messages")
            else "Not provided"
        )
        vitals = state.get("patient_info", {}).get("vitals", "Not provided")
        findings = state.get("visual_findings", "None")
        diagnosis = state.get("preliminary_diagnosis", "Inconclusive")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "user",
                    f"SYMPTOMS: {symptoms}\nVITALS: {vitals}\nIMAGING: {findings}\nDIAGNOSIS: {diagnosis}",
                ),
            ]
        )

        chain = prompt | self.llm
        response = await chain.ainvoke({})

        state["soap_notes"] = response.content
        logger.info("UX: Generated professional SOAP notes.")

        return state
