"""
Uncertainty Calibrator - Human-in-the-Loop Trigger.
Analyzes internal diagnostic confidence and triggers doctor escalation if needed.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class UncertaintyCalibrator:
    def __init__(self, confidence_threshold: int = 85):
        self.threshold = confidence_threshold

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check if AI confidence is high enough for autonomous output."""
        confidence = state.get("confidence_score") or state.get(
            "triage_confidence", 100
        )

        # Penalize confidence if hallucination or correction was triggered
        if state.get("is_hallucinating"):
            confidence -= 20
        if state.get("correction_count", 0) > 1:
            confidence -= 10

        state["calibrated_confidence"] = max(0, confidence)

        # Determine if human review is mandatory
        if state["calibrated_confidence"] < self.threshold:
            logger.warning(
                f"UNSTABLE CONFIDENCE ({state['calibrated_confidence']}% < {self.threshold}%). Escalating..."
            )
            state["requires_human_review"] = True
            state["safety_status"] = "PENDING_HUMAN_REVIEW"
            state["status"] = "Escalated for Clinical Oversight"

        return state
