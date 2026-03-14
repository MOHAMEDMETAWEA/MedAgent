"""
Triage Agent - Classifies Urgency and Extracts Symptoms.
Optimized for performance with lazy imports.
"""
import logging
import re
import json

from agents.interop.fhir_hl7_builder import FHIRClient

logger = logging.getLogger(__name__)

class TriageAgent:
    """
    Analyzes symptoms to determine urgency and structure patient data.
    """
    def __init__(self, model=None):
        from config import settings
        self.default_model = model or settings.OPENAI_MODEL
    
    def _get_llm(self, state: dict):
        from models.model_router import get_model
        model = state.get("model_used") or self.default_model
        return get_model(model_name=model, temperature=0.0)

    def _load_prompt(self, filename: str) -> str:
        from config import get_prompt_path
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise

    def process(self, state: dict):
        from langchain_core.messages import SystemMessage
        from utils.safety import sanitize_input, validate_medical_input
        from utils.medical_safety_framework import MedicalSafetyFramework
        from utils.audit_logger import AuditLogger
        
        logger.info("--- TRIAGE AGENT: ANALYZING SYMPTOMS & URGENCY ---")
        messages = state.get('messages', [])
        
        # Extract user input
        user_input = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                user_input += str(msg.content) + " "
        
        # Multimodal Integration
        visual_findings = state.get("visual_findings", {})
        if visual_findings:
            user_input += f"\n[VISUAL FINDINGS]: {visual_findings.get('visual_findings', '')}\n"
            user_input += f"Confidence: {visual_findings.get('confidence', 0.5)}, Severity: {visual_findings.get('severity_level', 'unknown')}"
        
        # FHIR EMR Integration
        fhir_id = state.get("fhir_id")
        if fhir_id:
            logger.info(f"--- TRIAGE AGENT: PULLING EMR DATA FOR {fhir_id} ---")
            fhir_client = FHIRClient()
            bg = fhir_client.fetch_patient_background(fhir_id)
            if "error" not in bg:
                emr_text = f"\n[EMR BACKGROUND]: Conditions: {', '.join(bg['conditions'])}, Medications: {', '.join(bg['medications'])}"
                user_input += emr_text
                logger.info("Successfully integrated EMR background.")

        # Validation
        user_input = sanitize_input(user_input)
        is_valid, error = validate_medical_input(user_input)
        if not is_valid:
            return {
                "patient_info": {"summary": f"Invalid input: {error}", "status": "error"},
                "next_step": "end"
            }

        # Regulatory Risk Classification
        risk_level = MedicalSafetyFramework.classify_risk(user_input)
        mandatory_disclaimer = MedicalSafetyFramework.get_mandatory_disclaimer(risk_level)
        
        try:
            prompt_template = self._load_prompt('triage_agent.txt')
            system_msg = SystemMessage(content=prompt_template)
            llm = self._get_llm(state)
            response = llm.invoke([system_msg] + list(messages))
            content = response.content
            
            # Parse Urgency (Map framework risk to agent urgency)
            urgency = risk_level.upper()
            if urgency == "EMERGENCY":
                logger.warning("!!! CRITICAL EMERGENCY DETECTED BY SAFETY FRAMEWORK !!!")

            is_sufficient = "STRUCTURED_CASE:" in content
            
            structured_data = {}
            if "STRUCTURED_CASE:" in content:
                try:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    structured_data = json.loads(content[start:end])
                except:
                    structured_data = {"summary": content}

            # Inject mandatory disclaimer into summary if emergency
            summary = structured_data.get("chief_complaint", content)
            if risk_level in ["Emergency", "High"]:
                summary = f"{mandatory_disclaimer}\n\n{summary}"

            # AUDIT LOGGING
            AuditLogger.log_agent_interaction(
                user_id=state.get("user_id", "unknown"),
                agent_name="TriageAgent",
                input_data=user_input,
                output_data=summary,
                model_used=self.default_model,
                risk_level=risk_level
            )

            return {
                "patient_info": {
                    "summary": summary,
                    "structured_case": structured_data,
                    "status": "complete" if is_sufficient else "incomplete",
                    "urgency": urgency,
                    "risk_level": risk_level,
                    "safety_disclaimer": mandatory_disclaimer
                },
                "critical_alert": (urgency == "EMERGENCY"),
                "risk_level": risk_level,
                "next_step": "knowledge" if is_sufficient else "end"
            }
        except Exception as e:
            logger.error(f"Triage error: {e}")
            return {
                "patient_info": {"status": "error", "summary": str(e)},
                "next_step": "end"
            }
