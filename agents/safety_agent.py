"""
Safety Agent - Final check for hazardous content.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings
from utils.safety import detect_critical_symptoms, detect_prompt_injection
import logging

logger = logging.getLogger(__name__)

class SafetyAgent:
    """
    Scans the final output for dangerous advice or hallucinations.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL, 
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def process(self, state: AgentState):
        print("--- SAFETY AGENT: FINAL GUARDRAIL ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        
        # 1. Rule-based checks
        is_critical, keywords = detect_critical_symptoms(diagnosis)
        is_injection, _ = detect_prompt_injection(diagnosis)
        
        if is_injection:
            return {
                "safety_status": "blocked",
                "preliminary_diagnosis": "Output blocked due to safety policy violation.",
                "next_step": "response"
            }

        # 2. LLM-based Safety Check
        prompt = (
            f"Review this medical content for safety:\n{diagnosis}\n\n"
            f"Does it contain harmful advice, self-harm encouragement, or fabricated treatments? "
            f"Output 'SAFE' or 'UNSAFE: <reason>'."
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Safety Agent. Protect the user."),
                HumanMessage(content=prompt)
            ])
            
            result = response.content
            if "UNSAFE" in result:
                logger.warning(f"Safety Agent blocked content: {result}")
                return {
                    "safety_status": "unsafe",
                    "preliminary_diagnosis": "The generated response was flagged as potentially unsafe and has been withheld. Please consult a doctor immediately.",
                    "next_step": "response"
                }
            
            return {"safety_status": "safe", "next_step": "response"}

        except Exception as e:
            logger.error(f"Safety checks error: {e}")
            return {"safety_status": "error", "next_step": "response"}
