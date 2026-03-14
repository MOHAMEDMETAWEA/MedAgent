"""
Safety Guardrail Agent - Highly Sensitive Clinical Filtering.
Acts as the final node in the LangGraph orchestration.
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from utils.medical_safety_framework import MedicalSafetyFramework

class SafetyGuardrailAgent(BaseAgent):
    def __init__(self):
        super().__init__("SafetyGuardrail")

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("--- Executing Final Clinical Safety Guardrail ---")
        
        final_response = state.get("final_response", "")
        if not final_response:
             # If no final response yet, check preliminary diagnosis
             final_response = state.get("preliminary_diagnosis", "")

        # 1. Perform risk classification
        risk_level = MedicalSafetyFramework.classify_risk(final_response)
        
        # 2. Inject mandatory disclaimer
        disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer(risk_level)
        
        # 3. Update state with safety metadata
        state["risk_level"] = risk_level
        if disclaimer not in final_response:
            state["final_response"] = f"{final_response}\n\n---\n{disclaimer}"
        
        # 4. Check for emergency trigger
        if risk_level == "Emergency":
            self.logger.warning("!!! EMERGENCY TRIGGERED BY FINAL GUARDRAIL !!!")
            state["critical_alert"] = True
            # For emergencies, we can even override the response if needed
            if "911" not in state["final_response"]:
                state["final_response"] = MedicalSafetyFramework.get_mandatory_disclaimer("Emergency")

        state["safety_verification_status"] = "PASSED"
        return state
