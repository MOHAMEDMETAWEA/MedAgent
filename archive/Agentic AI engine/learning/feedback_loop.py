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
        """Compute aggregate performance metrics with Weighted Role Influence."""
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

            # WEIGHTING LOGIC: Doctor feedback (2.0) vs Patient (1.0)
            total_weighted_sum = 0
            total_weight = 0

            stats = {}
            for row in results:
                role = getattr(row.role, "value", row.role)
                avg = float(row.avg_rating)
                count = row.total_count

                weight = 2.0 if role == "doctor" else 1.0
                total_weighted_sum += avg * count * weight
                total_weight += count * weight

                stats[role] = {"avg": avg, "count": count, "weight": weight}

            stats["system_weighted_score"] = (
                round(total_weighted_sum / total_weight, 2) if total_weight > 0 else 0.0
            )

            # Detect low-confidence clusters
            low_confidence_incidents = (
                db.query(Interaction)
                .filter(
                    Interaction.confidence_score < 0.6, Interaction.risk_level == "High"
                )
                .count()
            )

            stats["safety_alerts"] = low_confidence_incidents
            logger.info(
                f"RL Brain: Clinical trend analysis complete. Weighted Score: {stats['system_weighted_score']}"
            )
            return stats
        except Exception as e:
            logger.error(f"Feedback analysis fail: {e}")
            return {}
        finally:
            db.close()

    def get_latest_clinical_corrections(self, limit: int = 5) -> str:
        """Fetch the most recent high-quality doctor corrections for reasoning context."""
        db = self._db_factory()
        try:
            corrections = (
                db.query(Feedback)
                .filter(
                    Feedback.role == "doctor",
                    Feedback.rating >= 4,
                    Feedback.corrected_response_encrypted.isnot(None),
                )
                .order_by(Feedback.timestamp.desc())
                .limit(limit)
                .all()
            )

            from agents.governance_agent import GovernanceAgent

            gov = GovernanceAgent()

            correction_text = ""
            for fb in corrections:
                orig = gov.decrypt(fb.ai_response_encrypted)
                corr = gov.decrypt(fb.corrected_response_encrypted)
                correction_text += f"[PREVIOUS ERROR]: {orig[:100]}...\n[DOCTOR CORRECTION]: {corr}\n---\n"

            return correction_text
        except Exception as e:
            logger.error(f"Failed to fetch RL corrections: {e}")
            return ""
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
