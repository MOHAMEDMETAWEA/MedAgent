"""
Validation Agent - Cross-checks reasoning against evidence.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings
import logging

logger = logging.getLogger(__name__)

class ValidationAgent:
    """
    Verifies that the diagnosis is supported by the retrieved evidence.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL, 
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def process(self, state: AgentState):
        print("--- VALIDATION AGENT: CHECKING CONSISTENCY ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        knowledge = state.get('retrieved_docs', '')
        
        if not diagnosis:
            return {"validation_status": "skipped", "next_step": "safety"}

        prompt = (
            f"EVIDENCE (GUIDELINES):\n{knowledge}\n\n"
            f"PROPOSED DIAGNOSIS:\n{diagnosis}\n\n"
            f"TASK: Verify if the proposed diagnosis is supported by the Evidence. "
            f"If there are claims not in the evidence, flag them."
            f"Output 'VALID' if consistent, or 'ISSUE: <explanation>' if not."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Validation Agent. Strict fact-checking."),
                HumanMessage(content=prompt)
            ])
            
            result = response.content
            if "VALID" in result:
                return {"validation_status": "valid", "next_step": "safety"}
            else:
                # If invalid, we might want to loop back or tag it.
                # For this linear flow, we'll append the warning to the diagnosis
                new_diagnosis = diagnosis + "\n\n[VALIDATION WARNING]: " + result
                return {
                    "preliminary_diagnosis": new_diagnosis, 
                    "validation_status": "warning", 
                    "next_step": "safety"
                }

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {"validation_status": "error", "next_step": "safety"}
