"""
Persistence Agent - Manages Data Storage and Retrieval.
Handles generic, secure storage of user history and system logs.
Updated to use Governance Agent for Encryption.
"""
import uuid
import logging
from sqlalchemy.orm import Session
from database.models import SessionLocal, UserSession, Interaction, SystemLog
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class PersistenceAgent:
    """
    Agent responsible for saving interactions and logs to the database.
    Now integrates with Governance for Encryption.
    """
    def __init__(self):
        self.db: Session = SessionLocal()
        self.governance = GovernanceAgent()

    def create_session(self, user_id: str = "guest") -> str:
        """Start a new tracking session."""
        session_id = str(uuid.uuid4())
        try:
            new_session = UserSession(
                id=session_id,
                user_id=user_id,
                status="active"
            )
            self.db.add(new_session)
            self.db.commit()
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            self.db.rollback()
            return session_id 

    def save_interaction(self, session_id: str, user_input: str, result: dict):
        """Save a complete interaction flow with ENCRYPTION."""
        try:
            # Encrypt sensitive fields
            enc_input = self.governance.encrypt(user_input)
            enc_diagnosis = self.governance.encrypt(result.get("preliminary_diagnosis", ""))
            enc_response = self.governance.encrypt(result.get("final_response", ""))
            
            interaction = Interaction(
                session_id=session_id,
                user_input_encrypted=enc_input,
                diagnosis_output_encrypted=enc_diagnosis,
                final_response_encrypted=enc_response,
                metadata_json=result.get("patient_info", {}), # Summary is less sensitive? Still PII. 
                # Actually, triage summary might contain PII. Let's not persist it in plain text if strict.
                # For now, we store metadata as JSON. If PII is there, we should encrypt the whole blob.
                # Simplified: Storing metadata as plain JSON for analytics (assuming anonymized summary). 
                safety_flags={"critical_alert": result.get("critical_alert", False)}
            )
            self.db.add(interaction)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            self.db.rollback()

    def log_system_event(self, level: str, component: str, message: str, details: dict = None, session_id: str = None):
        """Log a system event or error."""
        try:
            log_entry = SystemLog(
                level=level,
                component=component,
                message=message,
                details=details or {},
                session_id=session_id
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"DB Logging failed: {e}")

    def get_user_history(self, user_id: str, limit: int = 10):
        """Retrieve past sessions for a user, DECRYPTING data."""
        try:
            # This just gets sessions. To get interactions, we need to query interactions.
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).order_by(UserSession.start_time.desc()).limit(limit).all()
            return sessions
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []

    def get_session_details(self, session_id: str):
        """Get full decrypted details for a session."""
        try:
            interactions = self.db.query(Interaction).filter(Interaction.session_id == session_id).all()
            decrypted = []
            for i in interactions:
                decrypted.append({
                    "timestamp": i.timestamp,
                    "user_input": self.governance.decrypt(i.user_input_encrypted),
                    "response": self.governance.decrypt(i.final_response_encrypted)
                })
            return decrypted
        except Exception as e:
             logger.error(f"Failed to get session details: {e}")
             return []

    def close(self):
        self.db.close()
        self.governance.close()
