"""
Safety Agent - Final check for hazardous content.
Uses Layer 5 structured prompt for risk stratification.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import detect_critical_symptoms, detect_prompt_injection
import logging
import json

logger = logging.getLogger(__name__)

class SafetyAgent:
    """
    Scans the final output for dangerous advice or hallucinations.
    Uses Layer 5 structured prompt for risk classification and red flag detection.
    """
    def __init__(self, model=None):
        self.default_model = model or settings.OPENAI_MODEL
    
    def _get_llm(self, state: AgentState):
        model = state.get("model_used") or self.default_model
        return ChatOpenAI(model=model, temperature=0.0, api_key=settings.OPENAI_API_KEY)

    def _load_prompt(self, filename: str) -> str:
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def process(self, state: AgentState):
        logger.info("--- SAFETY AGENT: LAYER 5 RISK STRATIFICATION ---")
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

        # 2. Load and use structured Layer 5 prompt template
        template = self._load_prompt('safety_agent.txt')
        if template:
            prompt = template.replace("{content_to_check}", diagnosis)
        else:
            # Fallback to inline prompt
            prompt = (
                f"Review this medical content for safety:\n{diagnosis}\n\n"
                f"Does it contain harmful advice, self-harm encouragement, or fabricated treatments? "
                f"Output 'SAFE' or 'UNSAFE: <reason>'."
            )

        try:
            llm = self._get_llm(state)
            response = llm.invoke([
                SystemMessage(content="You are a Medical Safety and Risk Stratification Agent (Layer 5). Protect the user. Output strict JSON."),
                HumanMessage(content=prompt)
            ])
            
            result = response.content
            
            # Try to parse structured JSON output from Layer 5 prompt
            risk_level = "LOW"
            red_flags = []
            safety_status = "safe"
            
            try:
                if "{" in result:
                    start = result.find("{")
                    end = result.rfind("}") + 1
                    parsed = json.loads(result[start:end])
                    risk_level = parsed.get("risk_level", "LOW")
                    red_flags = parsed.get("red_flags_detected", [])
                    safety_status = parsed.get("safety_status", "SAFE").lower()
                else:
                    # Fallback: parse SAFE/UNSAFE from text
                    if "UNSAFE" in result:
                        safety_status = "unsafe"
                    else:
                        safety_status = "safe"
            except (json.JSONDecodeError, ValueError):
                if "UNSAFE" in result:
                    safety_status = "unsafe"

            # Override risk_level if heuristic detected critical keywords
            if is_critical:
                risk_level = "CRITICAL" if risk_level not in ("HIGH", "CRITICAL") else risk_level
                
            if safety_status == "unsafe":
                logger.warning(f"Safety Agent blocked content: {result}")
                return {
                    "safety_status": "unsafe",
                    "risk_level": risk_level,
                    "red_flags": red_flags,
                    "preliminary_diagnosis": "The generated response was flagged as potentially unsafe and has been withheld. Please consult a doctor immediately.",
                    "critical_alert": True,
                    "next_step": "response"
                }
            
            # Set critical_alert for HIGH/CRITICAL risk levels
            is_high_risk = risk_level in ("HIGH", "CRITICAL")
            
            return {
                "safety_status": "safe",
                "risk_level": risk_level,
                "red_flags": red_flags,
                "critical_alert": is_high_risk or is_critical,
                "next_step": "response"
            }

        except Exception as e:
            logger.error(f"Safety checks error: {e}")
            return {"safety_status": "error", "next_step": "response"}
