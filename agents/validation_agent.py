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
        print("--- VALIDATION AGENT: LAYER 7 HALLUCINATION PREVENTION ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        knowledge = state.get('retrieved_docs', '')
        patient_info = state.get('patient_info', {})
        patient_summary = patient_info.get('summary', '')
        
        if not diagnosis:
            return {"validation_status": "skipped", "next_step": "safety"}

        prompt = (
            f"EVIDENCE (RETRIEVED GUIDELINES):\n{knowledge}\n\n"
            f"PATIENT SYMPTOMS:\n{patient_summary}\n\n"
            f"PROPOSED DIAGNOSIS:\n{diagnosis}\n\n"
            f"TASK — Layer 7 Validation Checklist:\n"
            f"Evaluate the proposed diagnosis against ALL of these criteria:\n"
            f"1. SYMPTOM-BASED: Is the reasoning directly based on the reported symptoms?\n"
            f"2. KNOWLEDGE-SUPPORTED: Is the reasoning supported by the retrieved evidence/guidelines?\n"
            f"3. MEDICALLY LOGICAL: Is the reasoning medically coherent and logical?\n"
            f"4. SAFETY CHECK: Are unsafe or unsupported conclusions avoided?\n"
            f"5. UNCERTAINTY: Is clinical uncertainty expressed where evidence is insufficient?\n\n"
            f"For each criterion, output PASS or FAIL with a brief explanation.\n"
            f"Final verdict: 'VALID' if all pass, or 'ISSUE: <explanation>' if any fail.\n"
            f"If uncertain about any claim, flag it explicitly — never fabricate diagnoses, statistics, or medical facts."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Validation Agent (Layer 7 — Hallucination Prevention). Perform strict fact-checking against evidence. Never fabricate medical facts."),
                HumanMessage(content=prompt)
            ])
            
            result = response.content
            if "VALID" in result and "ISSUE" not in result:
                return {"validation_status": "valid", "next_step": "safety"}
            else:
                # If invalid, append the warning to the diagnosis
                new_diagnosis = diagnosis + "\n\n[VALIDATION WARNING — Layer 7]: " + result
                return {
                    "preliminary_diagnosis": new_diagnosis, 
                    "validation_status": "warning", 
                    "next_step": "safety"
                }

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {"validation_status": "error", "next_step": "safety"}
