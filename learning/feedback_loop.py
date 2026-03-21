"""
Feedback Analysis & RL Loop - The System Quality Brain.
Tracks clinical performance trends and identifies model regression.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import func

from database.models import Feedback, Interaction, SessionLocal

logger = logging.getLogger(__name__)


class FeedbackRLLoop:
    def __init__(self):
        self._db_factory = SessionLocal

    def analyze_clinical_trends(self, limit: int = 100) -> Dict[str, Any]:
        """Compute aggregate performance metrics from doctor feedback."""
        db = self._db_factory()
        try:
            # Aggregate rating by role
            results = (
                db.query(
                    Feedback.role,
                    func.avg(Feedback.rating).label("avg_rating"),
                    func.count(Feedback.id).label("total_count"),
                )
                .group_by(Feedback.role)
                .all()
            )

            stats = {
                row.role: {"avg": float(row.avg_rating), "count": row.total_count}
                for row in results
            }

            # Detect low-confidence clusters (Potential Hallucinations)
            low_confidence_incidents = (
                db.query(Interaction)
                .filter(
                    Interaction.confidence_score < 0.6, Interaction.risk_level == "High"
                )
                .count()
            )

            stats["safety_alerts"] = low_confidence_incidents
            logger.info("RL Brain: Clinical trend analysis complete.")
            return stats
        except Exception as e:
            logger.error(f"Feedback analysis fail: {e}")
            return {}
        finally:
            db.close()

    def identify_learning_nodes(self) -> List[int]:
        """Find interactions where doctors corrected the AI - Prime for Fine-Tuning."""
        db = self._db_factory()
        try:
            corrections = (
                db.query(Feedback.interaction_id)
                .filter(
                    Feedback.corrected_response_encrypted.isnot(None),
                    Feedback.rating >= 4,  # Extract the 'gold' standard
                )
                .limit(50)
                .all()
            )
            return [c[0] for c in corrections if c[0]]
        finally:
            db.close()


# Singleton Instance
feedback_loop = FeedbackRLLoop()
