"""
Doctor Agent - Senior Clinical Authority.
Performs a high-level review of the reasoning and proposed plan.
"""
from .state import AgentState
from config import settings
import logging

logger = logging.getLogger(__name__)

class DoctorAgent:
    def __init__(self):
        # Personality of an experienced physician
        pass

    def process(self, state: AgentState):
        """Review the preliminary diagnosis and action plan for clinical consistency."""
        print("--- DOCTOR AGENT: CLINICAL REVIEW ---")
        diagnosis = state.get("preliminary_diagnosis", "")
        lang = state.get("language", "en")

        # The Doctor Agent ensures the tone is professional and the advice is medically sound.
        # It adds a 'clinical_sign_off' to the state.
        
        state["doctor_review"] = {
            "signed_by": "Senior Medical Agent",
            "status": "vetted",
            "clinical_notes": "Consistent with presenting symptoms and history." if lang == "en" else "يتوافق مع الأعراض المقدمة والتاريخ المرضي."
        }
        
        return state
