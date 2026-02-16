"""
Human Review Agent - Manages the interaction between AI and Human Reviewers.
"""
import logging
from database.models import SessionLocal, Interaction, ReviewStatus
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class HumanReviewAgent:
    """
    Manages flagged content and reviewer feedback.
    Acts as the 'Human Review Agent' in the multi-agent system.
    """
    def __init__(self):
        self.db = SessionLocal()
        self.governance = GovernanceAgent()

    def get_flagged_interactions(self):
        """Retrieve items requiring human review."""
        try:
            return self.db.query(Interaction).filter(Interaction.requires_human_review == True).all()
        except Exception as e:
            logger.error(f"Failed to fetch flagged items: {e}")
            return []

    def process_review_action(self, interaction_id: int, status: ReviewStatus, comment: str):
        """Update an interaction based on human review."""
        try:
            interaction = self.db.query(Interaction).filter(Interaction.id == interaction_id).first()
            if interaction:
                interaction.review_status = status
                interaction.reviewer_comment = comment
                interaction.requires_human_review = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to process review action: {e}")
            self.db.rollback()
            return False
