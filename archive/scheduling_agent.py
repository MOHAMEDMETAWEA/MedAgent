"""
Scheduling Agent - Local Clinic Coordinator.
Manages internal appointment slots and local registration.
"""
from .state import AgentState
from agents.persistence_agent import PersistenceAgent
import logging

logger = logging.getLogger(__name__)

class SchedulingAgent:
    def __init__(self):
        self.persistence = PersistenceAgent()

    def process(self, state: AgentState):
        """Handle internal clinic scheduling intents."""
        logger.info("--- SCHEDULING AGENT: LOCAL APPOINTMENTS ---")
        user_input = state.get('messages', [])[-1].content.lower() if state.get('messages') else ""
        
        # Local scheduling logic (e.g., booking in the internal 'medagent.db')
        if any(kw in user_input for kw in ["book", "appointment", "reserve", "حجز", "موعد"]):
            # Trigger persistence of appointment request
            session_id = state.get("session_id", "local-session")
            user_id = state.get("user_id", "guest")
            
            # Logic to save to local appointments table
            # (Assuming a local table 'appointments' exists or will be managed by Persistence)
            state["appointment_status"] = "Local Slot Requested"
            
        return state
