"""
Clinical Review Agent - Manages Human-in-the-Loop (HITL) validation for high-risk cases.
"""
import logging
import json
from database.models import AIAuditLog, Interaction, SessionLocal, ReviewStatus

logger = logging.getLogger(__name__)

class ClinicalReviewAgent:
    def __init__(self):
        pass

    def process(self, state: dict):
        """
        Standard entry point for the LangGraph orchestrator.
        Flags any case routed here for mandatory human review.
        """
        return self.process_high_risk_case(state)

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
            "hitl_active": True,
            "requires_human_review": True,
            "final_response": f"⚠️ This case has been flagged for clinical review due to high risk ({state.get('risk_level', 'High')}). A qualified clinician will review before any recommendations are released."
        }

    def submit_review(self, interaction_id: int, action: str, comment: str):
        """Updates the interaction status based on human doctor feedback."""
        with SessionLocal() as db:
            try:
                interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
                if not interaction:
                    return {"status": "error", "message": f"Interaction {interaction_id} not found"}
                
                if action == "approve":
                    interaction.review_status = ReviewStatus.APPROVED
                elif action == "reject":
                    interaction.review_status = ReviewStatus.REJECTED
                elif action == "escalate":
                    interaction.review_status = ReviewStatus.ESCALATED
                
                interaction.review_notes = comment
                db.commit()
                
                logger.info(f"HITL Review: Interaction {interaction_id} -> {action} by clinician.")
                return {"status": "success", "action": action, "interaction_id": interaction_id}
            except Exception as e:
                db.rollback()
                logger.error(f"Submit review error: {e}")
                return {"status": "error", "message": str(e)}

