import datetime
import json
import logging
from typing import Any, Dict, List

from sqlalchemy import func, select

from agents.governance_agent import GovernanceAgent
from database.models import AsyncSessionLocal, Feedback, Interaction, UserRole

logger = logging.getLogger(__name__)


class RLHFPipeline:
    """
    RLHF Learning Pipeline for MEDAgent.
    - Collects doctor and patient feedback.
    - Filters high-quality doctor corrections for medical reasoning.
    - Uses patient feedback for UX and clarity improvements.
    - Suggests prompt optimizations.
    """

    def __init__(self):
        self.governance = GovernanceAgent()

    async def collect_training_data(self, min_rating: int = 4):
        """
        Step 1 & 2: Collect and Filter High-Quality Doctor Feedback.
        Filters for feedback where role == doctor AND rating >= min_rating.
        """
        async with AsyncSessionLocal() as db:
            try:
                # We want doctor feedback with high ratings or corrections
                stmt = (
                    select(Feedback)
                    .filter(Feedback.role == "doctor", Feedback.rating >= min_rating)
                    .order_by(Feedback.timestamp.desc())
                )

                res = await db.execute(stmt)
                feedback_items = res.scalars().all()

                training_dataset = []
                for fb in feedback_items:
                    # Decrypt original AI response and doctor correction
                    original_ai = self.governance.decrypt(fb.ai_response_encrypted)
                    correction = (
                        self.governance.decrypt(fb.corrected_response_encrypted)
                        if fb.corrected_response_encrypted
                        else None
                    )
                    comment = (
                        self.governance.decrypt(fb.comment_encrypted)
                        if fb.comment_encrypted
                        else ""
                    )

                    if correction:
                        training_dataset.append(
                            {
                                "input": original_ai,
                                "output": correction,
                                "metadata": {
                                    "feedback_id": fb.id,
                                    "rating": fb.rating,
                                    "comment": comment,
                                    "source": "doctor_correction",
                                },
                            }
                        )
                    elif fb.rating == 5:
                        # High quality output without correction is also good for positive reinforcement
                        training_dataset.append(
                            {
                                "input": "N/A",  # Original prompt would be better if we linked to Interaction
                                "output": original_ai,
                                "metadata": {
                                    "feedback_id": fb.id,
                                    "rating": fb.rating,
                                    "source": "doctor_approved",
                                },
                            }
                        )

                return training_dataset
            except Exception as e:
                logger.error(f"RLHF Pipeline: Data collection failed: {e}")
                return []

    async def get_ux_improvements(self):
        """
        Phase 4: Process Patient Feedback for UX improvements.
        Focuses on clarity, tone, and communication style.
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    select(Feedback)
                    .filter(Feedback.role == "patient")
                    .order_by(Feedback.timestamp.desc())
                    .limit(100)
                )

                res = await db.execute(stmt)
                patient_feedback = res.scalars().all()

                insights = []
                for fb in patient_feedback:
                    if fb.rating <= 3:
                        comment = (
                            self.governance.decrypt(fb.comment_encrypted)
                            if fb.comment_encrypted
                            else "No comment"
                        )
                        insights.append(
                            {
                                "rating": fb.rating,
                                "comment": comment,
                                "timestamp": fb.timestamp,
                            }
                        )
                return insights
            except Exception as e:
                logger.error(f"RLHF Pipeline: UX insight generation failed: {e}")
                return []

    def generate_prompt_optimization_suggestions(self, training_data: List[Dict]):
        """
        Phase 6: Suggest dynamic prompt improvements based on gathered data.
        In a full implementation, this could call an LLM to analyze the corrections.
        """
        if not training_data:
            return "No enough high-quality data to suggest optimizations."

        suggestions = []
        corrections_count = sum(
            1
            for item in training_data
            if item["metadata"]["source"] == "doctor_correction"
        )

        if corrections_count > 0:
            suggestions.append(
                f"Found {corrections_count} doctor corrections. Consider updating reasoning prompts to include these edge cases."
            )

        return suggestions

    async def run_learning_cycle(self):
        """
        Phase 10: Sequential periodic learning cycle.
        """
        logger.info("Starting RLHF Learning Cycle...")

        # 1. Collect medical reasoning data (Doctor)
        training_data = await self.collect_training_data()

        # 2. Collect UX insights (Patient)
        ux_insights = await self.get_ux_improvements()

        # 3. Generate suggestions
        suggestions = self.generate_prompt_optimization_suggestions(training_data)

        report = {
            "cycle_timestamp": datetime.datetime.utcnow().isoformat(),
            "new_training_samples": len(training_data),
            "negative_ux_signals": len(ux_insights),
            "suggested_prompt_updates": suggestions,
        }

        logger.info(f"RLHF Learning Cycle Complete: {report}")
        return report


# Singleton instance
rlhf_pipeline = RLHFPipeline()
