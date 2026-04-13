"""
Human Review Agent - Manages the interaction between AI and Human Reviewers.
"""

import logging

from agents.governance_agent import GovernanceAgent
from database.models import Interaction, ReviewStatus, SessionLocal

logger = logging.getLogger(__name__)


class HumanReviewAgent:
    """
    Manages flagged content and reviewer feedback.
    Acts as the 'Human Review Agent' in the multi-agent system.
    """

    def __init__(self):
        self.governance = GovernanceAgent()

    def get_flagged_interactions(self):
        """Retrieve items requiring human review."""
        db = SessionLocal()
        try:
            return (
                db.query(Interaction)
                .filter(Interaction.requires_human_review == True)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to fetch flagged items: {e}")
            return []
        finally:
            db.close()

    def process_review_action(
        self, interaction_id: int, status: ReviewStatus, comment: str
    ):
        """Update an interaction based on human review."""
        db = SessionLocal()
        try:
            interaction = (
                db.query(Interaction).filter(Interaction.id == interaction_id).first()
            )
            if interaction:
                interaction.review_status = status
                interaction.reviewer_comment = comment
                interaction.requires_human_review = False
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to process review action: {e}")
            db.rollback()
            return False
        finally:
            db.close()
