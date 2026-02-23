"""
Knowledge Agent - Wrapper around Medical Retriever.
"""
from rag.retriever import MedicalRetriever
from .state import AgentState
import logging

logger = logging.getLogger(__name__)

class KnowledgeAgent:
    """
    Retrieves verified medical information to ground the reasoning.
    """
    def __init__(self):
        self.retriever = MedicalRetriever()

    def process(self, state: AgentState):
        logger.info("--- KNOWLEDGE AGENT: RETRIEVING CLINICAL GUIDELINES ---")
        patient_summary = state.get('patient_info', {}).get('summary', '')
        
        if not patient_summary:
            return {"retrieved_docs": "", "next_step": "reasoning"}

        try:
            # We can refine the query here if needed
            knowledge = self.retriever.retrieve(patient_summary)
            return {
                "retrieved_docs": knowledge,
                "next_step": "reasoning"
            }
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            return {
                "retrieved_docs": "Error retrieving medical guidelines. Proceeding with caution.",
                "next_step": "reasoning"
            }
