"""
Safety Agent - Final check for hazardous content.
Optimized for performance with lazy imports.
"""
import logging
import json

logger = logging.getLogger(__name__)

class SafetyAgent:
    def __init__(self, model=None):
        from config import settings
        self.default_model = model or settings.OPENAI_MODEL
    
    def _get_llm(self, state: dict):
        from langchain_openai import ChatOpenAI
        from config import settings
        model = state.get("model_used") or self.default_model
        return ChatOpenAI(model=model, temperature=0.0, api_key=settings.OPENAI_API_KEY)

    def _load_prompt(self, filename: str) -> str:
        from config import get_prompt_path
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def process(self, state: dict):
        from langchain_core.messages import SystemMessage, HumanMessage
        from utils.safety import detect_critical_symptoms, detect_prompt_injection
        
        logger.info("--- SAFETY AGENT: LAYER 5 RISK STRATIFICATION ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        
        is_critical, keywords = detect_critical_symptoms(diagnosis)
        is_injection, _ = detect_prompt_injection(diagnosis)
        
        if is_injection:
            return {
                "safety_status": "blocked",
                "preliminary_diagnosis": "Output blocked due to safety policy violation.",
                "next_step": "response"
            }

        template = self._load_prompt('safety_agent.txt')
        if template:
            prompt = template.replace("{content_to_check}", diagnosis)
        else:
            prompt = f"Review this medical content for safety:\n{diagnosis}\nOutput 'SAFE' or 'UNSAFE'."

        try:
            llm = self._get_llm(state)
            response = llm.invoke([
                SystemMessage(content="You are a Medical Safety Agent (Layer 5). Protect the user. Output strict JSON."),
                HumanMessage(content=prompt)
            ])
            
            result = response.content
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
                    safety_status = "unsafe" if "UNSAFE" in result else "safe"
            except:
                safety_status = "unsafe" if "UNSAFE" in result else "safe"

            if is_critical:
                risk_level = "CRITICAL" if risk_level not in ("HIGH", "CRITICAL") else risk_level
                
            if safety_status == "unsafe":
                return {
                    "safety_status": "unsafe",
                    "risk_level": risk_level,
                    "red_flags": red_flags,
                    "preliminary_diagnosis": "flagged as potentially unsafe.",
                    "critical_alert": True,
                    "next_step": "response"
                }
            
            return {
                "safety_status": "safe",
                "risk_level": risk_level,
                "red_flags": red_flags,
                "critical_alert": risk_level in ("HIGH", "CRITICAL") or is_critical,
                "next_step": "response"
            }

        except Exception as e:
            logger.error(f"Safety checks error: {e}")
            return {"safety_status": "error", "next_step": "response"}
