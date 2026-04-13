"""
Validation Agent - Cross-checks reasoning against evidence.
Optimized for performance with lazy imports.
"""

import logging

logger = logging.getLogger(__name__)


class ValidationAgent:
    def __init__(self, model=None):
        from config import settings

        self.default_model = model or settings.OPENAI_MODEL

    def _get_llm(self, state: dict):
        from models.model_router import get_model

        model = state.get("model_used") or self.default_model
        return get_model(model_name=model, temperature=0.0)

    def process(self, state: dict):
        from langchain_core.messages import HumanMessage, SystemMessage

        from config import settings

        logger.info("--- VALIDATION AGENT: LAYER 7 HALLUCINATION PREVENTION ---")
        diagnosis = state.get("preliminary_diagnosis", "")
        knowledge = state.get("retrieved_docs", "")
        patient_summary = state.get("patient_info", {}).get("summary", "")

        if not diagnosis:
            return {"validation_status": "skipped", "next_step": "safety"}

        prompt = (
            f"EVIDENCE:\n{knowledge}\n\n"
            f"PATIENT SYMPTOMS:\n{patient_summary}\n\n"
            f"PROPOSED DIAGNOSIS:\n{diagnosis}\n\n"
            f"Verdict: 'VALID' or 'ISSUE: <explanation>'."
        )

        try:
            llm = self._get_llm(state)
            response = llm.invoke(
                [
                    SystemMessage(
                        content="You are a Medical Validation Agent. Fact-check against evidence."
                    ),
                    HumanMessage(content=prompt),
                ]
            )

            result = response.content
            if "VALID" in result and "ISSUE" not in result:
                return {"validation_status": "valid"}
            else:
                logger.warning(f"VALIDATION ISSUE DETECTED: {result}")
                return {"validation_status": "invalid", "retry_reason": result}
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {"validation_status": "error"}
