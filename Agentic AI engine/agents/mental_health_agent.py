"""
Aria - The Mental Health & Psychiatric Specialist Agent.
Focuses on psychological well-aware, trauma-informed care, and crisis screening.
"""

import logging
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate

from models.model_router import get_model

logger = logging.getLogger(__name__)


class MentalHealthAgent:
    def __init__(self):
        self.llm = get_model()
        self.system_prompt = """
        You are "Aria", a compassionate Clinical Psychologist and Psychiatrist.
        You provide trauma-informed, empathetic mental health support and clinical screening.
        
        RULES:
        1. Never diagnose complex psychiatric disorders definitively; provide 'clinical impressions'.
        2. Always screen for suicide/self-harm risk (Emergency Escalation).
        3. Use open-ended, non-judgmental language.
        4. Focus on 'Coping Mechanisms' and 'Therapeutic Next Steps'.
        5. If a crisis is detected, provide the National Suicide Prevention Lifeline immediately.
        """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized reasoning for mental health cases."""
        patient_input = (
            state.get("messages", [None])[-1].content if state.get("messages") else ""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "user",
                    f"Analyze patient state and provide compassionate guidance: {patient_input}",
                ),
            ]
        )

        chain = prompt | self.llm
        response = await chain.ainvoke({})

        state["mental_health_score"] = self._calculate_basic_distress(response.content)
        state["specialty_recommendation"] = response.content

        return state

    def _calculate_basic_distress(self, text: str) -> int:
        # Simplified distress mapping for audit
        low = ["calm", "stable", "improving"]
        high = ["hopeless", "panic", "severe", "crisis"]
        if any(h in text.lower() for h in high):
            return 8
        if any(l in text.lower() for l in low):
            return 2
        return 5
