"""
Verification Agent - Validates Doctor Credentials.
"""
import logging
from agents.persistence_agent import PersistenceAgent
from config import settings

logger = logging.getLogger(__name__)

class VerificationAgent:
    """
    Verification Agent:
    - Validates medical license formats (simulated).
    - Updates user verification status via Persistence.
    """
    def __init__(self):
        self.persistence = PersistenceAgent()

    def verify_doctor_credentials(self, user_id: str, license_number: str, specialization: str, country: str):
        """
        In a real system, this would call a government/medical board API.
        For MEDAgent, we perform format validation and auto-approve for specific demo formats.
        """
        print(f"--- VERIFICATION AGENT: VALIDATING CREDENTIALS FOR {user_id} ---")
        
        # Simple simulation logic
        if not license_number or len(license_number) < 5:
            return False, "Invalid license number format."
        
        if not specialization:
            return False, "Specialization must be provided."
            
        # Simulated validation success
        success = self.persistence.verify_doctor(user_id, license_number, specialization)
        if success:
            self.persistence.log_system_event("INFO", "VerificationAgent", f"Doctor {user_id} verified successfully.")
            return True, "Verification successful."
        
        return False, "Failed to update verification status in database."
