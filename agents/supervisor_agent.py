"""
Supervisor Agent - System Health & Self-Healing.
Monitors agent activities and logs system health.
"""
import logging
import datetime
from agents.persistence_agent import PersistenceAgent
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    Supervisor Agent.
    Responsibilities:
    - Monitor system health
    - Log critical errors
    - Trigger self-healing (if applicable)
    """
    def __init__(self):
        self.persistence = PersistenceAgent()
        self.governance = GovernanceAgent() # For secure logging

    def log_event(self, level: str, message: str, details: dict = None):
        """Log a system event securely."""
        try:
            timestamp = datetime.datetime.utcnow().isoformat()
            log_entry = f"[{timestamp}] [{level}] {message}"
            if details:
                log_entry += f" | Details: {details}"
            
            # Log to file/console
            if level == "ERROR":
                logger.error(log_entry)
            elif level == "WARNING":
                logger.warning(log_entry)
            else:
                logger.info(log_entry)
                
            # Log to DB via Persistence
            self.persistence.log_system_event(level, "Supervisor", message, details)
        except Exception as e:
            logger.error(f"Supervisor failed to log event: {e}")

    def health_check(self):
        """
        Perform a health check of critical components.
        """
        status = {
            "database": "Unknown",
            "openai_api": "Unknown",
            "agents": "Active" # Assuming they loaded if this runs
        }
        
        # Check DB
        try:
            # Simple query to check connectivity
            from database.models import SystemLog
            self.persistence.db.query(SystemLog).first()
            status["database"] = "Healthy"
        except Exception:
            status["database"] = "Unhealthy"
            
        return status
