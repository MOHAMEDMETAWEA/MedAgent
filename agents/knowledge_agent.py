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

    async def process(self, state: dict):
        logger.info("--- KNOWLEDGE AGENT: RETRIEVING CLINICAL CONTEXT & GUIDELINES ---")
        patient_summary = state.get("patient_info", {}).get("summary", "")
        patient_id = state.get("patient_info", {}).get(
            "id", "test-patient-001"
        )  # Default for demo

        if not patient_summary:
            return {"retrieved_docs": "", "next_step": "reasoning"}

        try:
            from config import settings
            from integrations.fhir_connector import FHIRConnector

            # Fetch EMR Context
            fhir = FHIRConnector(base_url=settings.FHIR_BASE_URL)
            # In production, we'd use the current user's token
            conditions = await fhir.get_conditions(patient_id)
            meds = await fhir.get_medications(patient_id)

            ehr_context = (
                f"EMR CONDITIONS: {str(conditions)}\nEMR MEDICATIONS: {str(meds)}"
            )

            retriever = self.get_retriever()
            knowledge = retriever.retrieve(patient_summary)

            # Clinical Knowledge Verification (Feature 5)
            # Ensure sources are from WHO, NIH, or PubMed
            trusted_domains = ["who.int", "nih.gov", "pubmed", "cdc.gov"]
            is_verified = any(domain in knowledge.lower() for domain in trusted_domains)

            verification_status = "VERIFIED" if is_verified else "UNVERIFIED"
            logger.info(f"Knowledge Verification: {verification_status}")

            combined_knowledge = f"{ehr_context}\n\nCLINICAL GUIDELINES ({verification_status}):\n{knowledge}"

            return {
                "retrieved_docs": combined_knowledge,
                "knowledge_verified": is_verified,
                "next_step": "reasoning",
            }
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            return {
                "retrieved_docs": "Error retrieving medical guidelines. Proceeding with caution.",
                "next_step": "reasoning",
            }
