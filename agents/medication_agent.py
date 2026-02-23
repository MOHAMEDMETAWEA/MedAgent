"""
Medication & Reminder Agent - Comprehensive Tracking Authority.
Handles Medication tracking, Reminders, and Health compliance.
"""
import logging
from .state import AgentState
from .persistence_agent import PersistenceAgent
from config import settings

logger = logging.getLogger(__name__)

class MedicationAgent:
    def __init__(self):
        self.persistence = PersistenceAgent()

    def process(self, state: AgentState):
        """
        Analyze user input for medication-related intents and update tracking.
        """
        logger.info("--- MEDICATION AGENT: PHARMACOLOGICAL REVIEW ---")
        user_input = state.get('messages', [])[-1].content.lower()
        user_id = state.get('user_id', 'guest')
        lang = state.get('language', 'en')

        # Simple Intent Detection
        if any(kw in user_input for kw in ["medication", "medicine", "pill", "dose", "drug", "دواء", "حبوب", "جرعة"]):
            state["status"] = "Updating medication records..."
            meds = self.get_medications(user_id)
            med_list = "\n".join([f"- {m['name']}: {m['dosage']} ({m['frequency']})" for m in meds]) if meds else "No active medications found."
            
            response = f"I am managing your medication profile. Here are your current active medications:\n{med_list}\n\nYou can add new medications or set reminders in the 'Meds & Reminders' tab."
            if lang == "ar":
                response = f"أنا أقوم بإدارة ملف الأدوية الخاص بك. إليك أدويتك الحالية:\n{med_list}\n\nيمكنك إضافة أدوية جديدة أو ضبط التذكيرات في علامة التبويب 'الأدوية والتذكيرات'."
            
            state["final_response"] = response
            state["next_step"] = "end"
            
        return state

    def add_medication(self, user_id: str, name: str, dosage: str, frequency: str):
        """Register a new medication."""
        return self.persistence.add_medication(user_id, name, dosage, frequency)

    def get_medications(self, user_id: str):
        """Retrieve active medications."""
        return self.persistence.get_medications(user_id)

    def add_reminder(self, user_id: str, title: str, time_str: str, med_id: int = None):
        """Add a health reminder."""
        return self.persistence.add_reminder(user_id, title, time_str, med_id)
