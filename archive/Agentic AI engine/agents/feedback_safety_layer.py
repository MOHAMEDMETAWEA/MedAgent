import logging
from typing import Any, Dict

from agents.verification_agent import VerificationAgent

logger = logging.getLogger(__name__)


class FeedbackSafetyLayer:
    """
    Enforces safety constraints on incoming feedback.
    - Validates doctor credentials for medical corrections.
    - Filters malicious or nonsensical feedback.
    """

    def __init__(self):
        self.verifier = VerificationAgent()

    async def validate_doctor_authority(self, user: dict) -> bool:
        """
        Phase 8: Ensure the user is a verified doctor before accepting reasoning overrides.
        """
        if user.get("role") != "doctor":
            return False

        # Call the VerificationAgent to check credential status
        # This is high authority verification
        is_verified = await self.verifier.verify_doctor(
            user.get("sub"), "SIMULATED_CREDENTIAL"
        )
        return is_verified.get("verified", False)

    def check_feedback_safety(self, rating: int, comment: str) -> bool:
        """
        Basic heuristic to prevent spam or malicious feedback.
        """
        if rating < 0 or rating > 5:
            return False

        if comment and len(comment) > 5000:
            # Excessive length might be an injection attempt
            return False

        return True


# Singleton
feedback_safety = FeedbackSafetyLayer()
