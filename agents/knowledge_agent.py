"""
Knowledge Agent - Wrapper around Medical Retriever.
Optimized for performance with lazy imports.
"""
import logging

logger = logging.getLogger(__name__)

class KnowledgeAgent:
    def __init__(self):
        # retriever is initialized only when needed
        self._retriever = None

    def get_retriever(self):
        if not self._retriever:
            from rag.retriever import MedicalRetriever
            self._retriever = MedicalRetriever()
        return self._retriever

    def process(self, state: dict):
        logger.info("--- KNOWLEDGE AGENT: RETRIEVING CLINICAL GUIDELINES ---")
        patient_summary = state.get('patient_info', {}).get('summary', '')
        
        if not patient_summary:
            return {"retrieved_docs": "", "next_step": "reasoning"}

        try:
            retriever = self.get_retriever()
            knowledge = retriever.retrieve(patient_summary)
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
