"""
Clinical Review Agent - Manages Human-in-the-Loop (HITL) validation for high-risk cases.
"""
import logging
import json
from database.models import AIAuditLog, SessionLocal, ReviewStatus

logger = logging.getLogger(__name__)

class ClinicalReviewAgent:
    def __init__(self):
        pass

    def process_high_risk_case(self, state: dict):
        """
        Flags a case specifically for doctor review.
        In a real-world system, this would trigger a notification and wait.
        For current orchestration, we flag the state.
        """
        logger.info("--- CLINICAL REVIEW AGENT: TRIGGERING HITL WORKFLOW ---")
        
        # Flag the state for the API/Frontend to pick up
        state["requires_human_review"] = True
        state["review_status"] = "pending"
        
        # Log this trigger in the audit trail
        from utils.audit_logger import AuditLogger
        AuditLogger.log_agent_interaction(
            user_id=state.get("user_id", "unknown"),
            agent_name="ClinicalReviewAgent",
            input_data="High-risk clinical trigger detected",
            output_data="Awaiting Doctor Validation",
            model_used="Human-in-the-Loop",
            confidence=1.0,
            risk_level=state.get("risk_level", "High")
        )

        return {
            "status": "Awaiting Clinical Review",
            "next_step": "end", # Pause execution until manual intervention
            "hitl_active": True
        }

    def submit_review(self, interaction_id: int, action: str, comment: str):
        """Updates the status based on human doctor feedback."""
        with SessionLocal() as db:
            # logic to update interaction/audit log
            pass
