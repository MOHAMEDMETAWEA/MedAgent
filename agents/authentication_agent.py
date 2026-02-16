"""
Authentication Agent - Secure Identity and Session Management.
"""
import logging
from agents.governance_agent import GovernanceAgent
from agents.persistence_agent import PersistenceAgent

logger = logging.getLogger(__name__)

class AuthenticationAgent:
    """
    Dedicated agent for secure user registration, login, and token management.
    Wraps Governance and Persistence for identity logic.
    """
    def __init__(self):
        self.governance = GovernanceAgent()
        self.persistence = PersistenceAgent()

    def register_new_user(self, **user_data):
        return self.persistence.register_user(**user_data)

    def validate_login(self, login_id, password, ip=None):
        user = self.persistence.get_user_by_login(login_id)
        if not user or not self.governance.verify_password(password, user.password_hash):
            if user:
                self.persistence.log_user_activity(user.id, "none", "failed", ip=ip)
            return None, "Invalid credentials"
        
        session_id = self.persistence.create_session(user_id=user.id)
        token = self.governance.create_access_token({"sub": user.id, "role": user.role, "name": user.username})
        
        self.persistence.log_user_activity(user.id, session_id, "success", ip=ip)
        return {
            "token": token,
            "session_id": session_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "full_name": self.governance.decrypt(user.full_name_encrypted)
            }
        }, None
