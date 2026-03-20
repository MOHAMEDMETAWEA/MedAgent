import logging
from typing import List, Dict
from sqlalchemy import select
from database.models import AsyncSessionLocal, Feedback, Interaction
from agents.governance_agent import GovernanceAgent

logger = logging.getLogger(__name__)

class DoctorFeedbackCollector:
    """
    Phase 1: Data Pipeline
    Responsible for collecting high-quality training data from doctor feedback.
    """
    def __init__(self):
        self.governance = GovernanceAgent()

    async def get_consensus_samples(self) -> List[Dict]:
        """
        Extracts cases from CaseWorkspace where consensus was reached.
        Highest-quality collective intelligence data.
        """
        from collaboration.case_workspace import case_workspace
        samples = []
        for case_id, case in case_workspace.active_cases.items():
            if case.get("consensus_reached"):
                samples.append({
                    "id": f"consensus-{case_id}",
                    "input": case["state"].get("symptoms", ""),
                    "output": case["final_diagnosis"],
                    "type": "consensus",
                    "rating": 5
                })
        return samples

    async def get_high_quality_samples(self, min_rating: int = 4) -> List[Dict]:
        """
        Collects feedback from doctors and combines with multi-doctor consensus.
        """
        consensus_data = await self.get_consensus_samples()
        
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(Feedback).filter(
                    Feedback.role == "doctor",
                    Feedback.rating >= min_rating
                ).order_by(Feedback.timestamp.desc())
                
                res = await db.execute(stmt)
                feedback_items = res.scalars().all()
                
                samples = consensus_data
                for fb in feedback_items:
                    # Decrypt original input/output
                    ai_response = self.governance.decrypt(fb.ai_response_encrypted)
                    correction = self.governance.decrypt(fb.corrected_response_encrypted) if fb.corrected_response_encrypted else None
                    interaction_context = await self._get_interaction_context(fb.case_id)
                    
                    if correction:
                        samples.append({
                            "id": fb.id,
                            "input": interaction_context or "Unknown symptoms",
                            "output": correction,
                            "type": "correction",
                            "rating": fb.rating
                        })
                    elif fb.rating == 5:
                        samples.append({
                            "id": fb.id,
                            "input": interaction_context or "Unknown symptoms",
                            "output": ai_response,
                            "type": "approved",
                            "rating": fb.rating
                        })
                
                logger.info(f"Pipeline: Collected {len(samples)} total clinical training samples.")
                return samples
                
            except Exception as e:
                logger.error(f"Data Pipeline Error: {e}")
                return []

    async def _get_interaction_context(self, case_id: str) -> str:
        """Helper to retrieve the initial patient input for a case."""
        if not case_id: return ""
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(Interaction).filter(Interaction.case_id == case_id).order_by(Interaction.timestamp.asc()).limit(1)
                res = await db.execute(stmt)
                interaction = res.scalars().first()
                if interaction:
                    return self.governance.decrypt(interaction.user_input_encrypted)
                return ""
            except:
                return ""

# Singleton Instance
data_pipeline = DoctorFeedbackCollector()
