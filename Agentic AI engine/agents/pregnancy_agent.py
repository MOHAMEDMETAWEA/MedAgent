"""
Maya - The Pregnancy & Maternity Specialist Agent.
Focuses on fetal development, maternal health, and pregnancy-safe protocols.
"""

import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate

from models.model_router import get_model

logger = logging.getLogger(__name__)


class PregnancyAgent:
    def __init__(self):
        self.llm = get_model()
        self.system_prompt = """
        You are "Maya", a compassionate OB/GYN and Maternity specialist.
        Your mission is to provide evidence-based, pregnancy-safe advice and emotional support.
        
        RULES:
        1. Always specify if a medication or procedure is Category A, B, C, D, or X.
        2. Focus on maternal nutrition, fetal milestones, and common pregnancy symptoms.
        3. Use a supportive, calm, and reassuring tone.
        4. Always mention: "Consult your obstetrician before making any changes."
        5. If 'Trimester' is known, tailor advice to specific fetal development markers.
        """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reasoning for maternity cases."""
        clinical_finding = state.get("preliminary_diagnosis", "")
        trimester = state.get("patient_info", {}).get("trimester", "Unknown")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "user",
                    f"Patient is in {trimester} trimester. Clinical finding: {clinical_finding}",
                ),
            ]
        )

        chain = prompt | self.llm
        response = await chain.ainvoke({})

        state["specialty_recommendation"] = response.content
        state["is_pregnancy_safe"] = "safe" in response.content.lower()

        return state
