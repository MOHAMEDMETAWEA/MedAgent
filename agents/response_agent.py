"""
Response Agent - Patient Communication Specialist.
Tailors the final output for clarity, empathy, and patient-centric formatting.
"""
from .state import AgentState
from config import settings
import logging

logger = logging.getLogger(__name__)

class ResponseAgent:
    def __init__(self):
        pass

    def process(self, state: AgentState):
        """Final polish of the system response for the user."""
        print("--- RESPONSE AGENT: FORMATTING & EMPATHY ---")
        final_response = state.get("final_response", "")
        lang = state.get("language", "en")
        
        # Add empathetic headers and clear formatting
        empathy_prefix = "We understand this situation can be difficult. " if lang == "en" else "نحن نتفهم أن هذا الموقف قد يكون صعباً. "
        
        if final_response and empathy_prefix not in final_response:
            state["final_response"] = f"{empathy_prefix}\n\n{final_response}"
            
        return state
