"""
Medical Hallucination Detector - Guardian of Clinical Truth.
Analyzes AI responses for factual consistency against retrieved medical knowledge.
"""

import logging
from typing import Any, Dict, List

from langchain.prompts import ChatPromptTemplate

from models.model_router import get_model

logger = logging.getLogger(__name__)


class HallucinationDetector:
    def __init__(self):
        self.llm = get_model()  # Usually a smaller, faster model for verification
        self.system_prompt = """
        You are a Critical Clinical Auditor.
        Your task is to detect "Hallucinations" (unsupported or contradictory medical claims) 
        in an AI's preliminary diagnosis by comparing it against retrieved Clinical Evidence.
        
        INPUTS:
        1. Preliminary Diagnosis (AI generated)
        2. Clinical Evidence (Trusted medical documents/CDSS guidelines)
        
        RULES:
        1. If the diagnosis contains a drug or treatment NOT supported by the evidence, flag as HALLUCINATION.
        2. If the diagnosis contradicts a known safe protocol in the evidence, flag as CRITICAL_CONFLICT.
        3. Output a 'Factual Integrity Score' (0-100).
        4. If score < 85, set 'is_hallucinating' to True.
        """

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the reasoning output against retrieved documents."""
        diagnosis = state.get("preliminary_diagnosis", "")
        evidence = state.get("retrieved_docs", "")

        if not diagnosis or not evidence:
            state["hallucination_score"] = 100
            return state

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", f"EVIDENCE: {evidence}\n\nDIAGNOSIS TO AUDIT: {diagnosis}"),
            ]
        )

        chain = prompt | self.llm
        response = await chain.ainvoke({})

        score = self._parse_score(response.content)
        state["hallucination_score"] = score
        state["hallucination_report"] = response.content
        state["is_hallucinating"] = score < 85

        if state["is_hallucinating"]:
            logger.warning(f"HALLUCINATION DETECTED! Integrity Score: {score}")
            state["validation_status"] = "invalid"  # Trigger correction loop
            state["retry_reason"] = (
                "Clinical hallucination detected in previous reasoning."
            )

        return state

    def _parse_score(self, text: str) -> int:
        import re

        match = re.search(r"Score:\s*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Fallback to keyword heuristic
        if "hallucination" in text.lower():
            return 50
        return 95
