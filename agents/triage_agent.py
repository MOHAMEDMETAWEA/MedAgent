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
        from langchain_openai import ChatOpenAI
        from config import settings
        model = state.get("model_used") or self.default_model
        return ChatOpenAI(model=model, temperature=0.0, api_key=settings.OPENAI_API_KEY)

    def _load_prompt(self, filename: str) -> str:
        from config import get_prompt_path
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise

    def process(self, state: dict):
        from langchain_core.messages import SystemMessage
        from utils.safety import sanitize_input, validate_medical_input, detect_critical_symptoms
        
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

        # Check for critical keywords
        is_critical, keywords = detect_critical_symptoms(user_input)
        
        try:
            prompt_template = self._load_prompt('triage_agent.txt')
            system_msg = SystemMessage(content=prompt_template)
            llm = self._get_llm(state)
            response = llm.invoke([system_msg] + list(messages))
            content = response.content
            
            # Parse Urgency
            urgency = "LOW"
            if "URGENCY: EMERGENCY" in content or is_critical:
                urgency = "EMERGENCY"
            elif "URGENCY: HIGH" in content:
                urgency = "HIGH"
            elif "URGENCY: MEDIUM" in content:
                urgency = "MEDIUM"

            is_sufficient = "STRUCTURED_CASE:" in content
            
            structured_data = {}
            if "STRUCTURED_CASE:" in content:
                try:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    structured_data = json.loads(content[start:end])
                except:
                    structured_data = {"summary": content}

            questions = []
            if "QUESTIONS:" in content:
                q_block = content.split("QUESTIONS:")[1].strip()
                questions = [q.strip() for q in q_block.split("\n") if q.strip()]

            return {
                "patient_info": {
                    "summary": structured_data.get("chief_complaint", content),
                    "structured_case": structured_data,
                    "status": "complete" if is_sufficient else "incomplete",
                    "urgency": urgency,
                    "clarification_questions": questions
                },
                "critical_alert": (urgency == "EMERGENCY"),
                "next_step": "knowledge" if is_sufficient else "end"
            }
        except Exception as e:
            logger.error(f"Triage error: {e}")
            return {
                "patient_info": {"status": "error", "summary": str(e)},
                "next_step": "end"
            }
