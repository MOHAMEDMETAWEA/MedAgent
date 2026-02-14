"""
Self-Improvement Agent.
Analyzes feedback and human review data to suggest improvements.
"""
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.models import SessionLocal, UserFeedback, Interaction, ReviewStatus
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class SelfImprovementAgent:
    """
    Monitors system performance via feedback and review logs.
    """
    def __init__(self):
        self.db: Session = SessionLocal()
        self.governance = GovernanceAgent()

    def analyze_feedback(self):
        """Analyze low-rated interactions for patterns."""
        try:
            # Find low ratings (1 or 2 stars)
            poor_feedback = self.db.query(UserFeedback).filter(UserFeedback.rating <= 2).all()
            if not poor_feedback:
                return "No negative feedback to analyze."
            
            report = "NEGATIVE FEEDBACK ANALYSIS:\n"
            for fb in poor_feedback:
                # Retrieve validation/safety flags for context
                assoc_interaction = self.db.query(Interaction).filter(Interaction.id == fb.interaction_id).first()
                flags = assoc_interaction.safety_flags if assoc_interaction else {}
                report += f"- Session {fb.session_id}: Rating {fb.rating}, Comment: {fb.comment}, Flags: {flags}\n"
            
            # In a real system, we'd use an LLM here to summarize and suggest prompt edits
            return report
        except Exception as e:
            logger.error(f"Feedback analysis failed: {e}")
            return "Error analyzing feedback."

    def process_human_reviews(self):
        """Learn from rejected/corrected outputs."""
        try:
            # Find Rejected interactions
            rejected = self.db.query(Interaction).filter(Interaction.review_status == ReviewStatus.REJECTED).all()
            if not rejected:
                return "No rejected interactions found."
            
            report = "HUMAN REVIEW LEARNINGS:\n"
            for item in rejected:
                input_text = self.governance.decrypt(item.user_input_encrypted)
                report += f"- Rejected Response for input '{input_text[:50]}...'. Reviewer Comment: {item.reviewer_comment}\n"
            
            return report
        except Exception as e:
            logger.error(f"Review processing failed: {e}")
            return "Error processing reviews."

    def generate_improvement_report(self):
        """Aggregate all learnings."""
        feedback_insights = self.analyze_feedback()
        review_insights = self.process_human_reviews()
        
        full_report = (
            "--- SELF-IMPROVEMENT REPORT ---\n"
            f"{feedback_insights}\n"
            f"{review_insights}\n"
            "-------------------------------\n"
        )
        return full_report
