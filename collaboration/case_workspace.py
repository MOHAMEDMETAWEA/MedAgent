import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ClinicalCaseWorkspace:
    """
    Phase 4: Multi-Doctor Collaboration System
    Responsibilities:
    - Manage shared patient cases between multiple clinicians.
    - Facilitate doctor commentary and peer review.
    - Implement a diagnosis voting and consensus system.
    """
    def __init__(self):
        self.active_cases = {}

    async def open_case(self, case_id: str, interaction_state: Dict[str, Any]):
        """Opens a case for multi-doctor review."""
        logger.info(f"Collaboration: Opening case {case_id} for clinical review.")
        self.active_cases[case_id] = {
            "state": interaction_state,
            "reviews": [],
            "votes": {}, # doctor_id -> diagnosis_id/vote
            "consensus_reached": False,
            "final_diagnosis": None,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def add_review_comment(self, case_id: str, doctor_id: str, comment: str):
        """Adds a clinical comment to a shared case workspace."""
        if case_id not in self.active_cases:
            return False
            
        self.active_cases[case_id]["reviews"].append({
            "doctor": doctor_id,
            "comment": comment,
            "time": datetime.utcnow().isoformat()
        })
        logger.info(f"Collaboration: Doctor {doctor_id} added a comment to {case_id}")
        return True

    async def cast_vote(self, case_id: str, doctor_id: str, diagnosis_choice: str):
        """Casts a doctor's vote on a proposed diagnosis."""
        if case_id not in self.active_cases:
            return False
            
        self.active_cases[case_id]["votes"][doctor_id] = diagnosis_choice
        logger.info(f"Collaboration: Doctor {doctor_id} voted for '{diagnosis_choice}' on {case_id}")
        
        # Check for consensus (e.g., Simple Majority or 2+ concordant votes)
        await self._evaluate_consensus(case_id)
        return True

    async def _evaluate_consensus(self, case_id: str):
        """Checks if enough doctors agree to finalize a diagnosis."""
        votes = list(self.active_cases[case_id]["votes"].values())
        if len(votes) >= 2: # Minimum quorum
            # Simple majority logic
            from collections import Counter
            counts = Counter(votes)
            top_choice, count = counts.most_common(1)[0]
            
            if count >= 2: # Consensus threshold
                self.active_cases[case_id]["consensus_reached"] = True
                self.active_cases[case_id]["final_diagnosis"] = top_choice
                logger.info(f"Collaboration: CONSENSUS REACHED for {case_id}. Final: {top_choice}")
                # In Phase 6, this consensus will feed back into the learning loop

# Singleton Instance
case_workspace = ClinicalCaseWorkspace()
