"""
Triage Agent - Classifies Urgency and Extracts Symptoms.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import sanitize_input, validate_medical_input, detect_critical_symptoms
import logging
import re

logger = logging.getLogger(__name__)

class TriageAgent:
    """
    Analyzes symptoms to determine urgency and structure patient data.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=0.0, # Strict for classification
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename: str) -> str:
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise

    def process(self, state: AgentState):
        print("--- TRIAGE AGENT: ANALYZING SYMPTOMS & URGENCY ---")
        messages = state.get('messages', [])
        
        # Extract user input
        user_input = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                user_input += str(msg.content) + " "
        
        # Multimodal Integration: Add visual findings to triage context
        visual_findings = state.get("visual_findings", {})
        if visual_findings:
            user_input += f"\n[VISUAL FINDINGS]: {visual_findings.get('visual_findings', '')}\n"
            user_input += f"Confidence: {visual_findings.get('confidence', 0.5)}, Severity: {visual_findings.get('severity_level', 'unknown')}"
        
        # Validation
        user_input = sanitize_input(user_input)
        is_valid, error = validate_medical_input(user_input)
        if not is_valid:
            return {
                "patient_info": {"summary": f"Invalid input: {error}", "status": "error"},
                "next_step": "end"
            }

        # Check for critical keywords heuristic first (Safety Layer 0)
        is_critical, keywords = detect_critical_symptoms(user_input)
        
        try:
            prompt_template = self._load_prompt('triage_agent.txt')
            system_msg = SystemMessage(content=prompt_template)
            response = self.llm.invoke([system_msg] + list(messages))
            content = response.content
            
            # Parse Urgency
            urgency = "LOW"
            if "URGENCY: EMERGENCY" in content or is_critical:
                urgency = "EMERGENCY"
            elif "URGENCY: HIGH" in content:
                urgency = "HIGH"
            elif "URGENCY: MEDIUM" in content:
                urgency = "MEDIUM"
                
            # If Emergency, we might want to short-circuit, but for now we pass to Reasoning/Response
            # taking note of the urgency.
            
            is_sufficient = "PATIENT SUMMARY:" in content
            
            summary = content
            if "PATIENT SUMMARY:" in content:
                summary = content.split("PATIENT SUMMARY:")[1].split("URGENCY:")[0].strip()

            return {
                "patient_info": {
                    "summary": summary,
                    "status": "complete" if is_sufficient else "incomplete",
                    "urgency": urgency,
                    "original_triage_output": content
                },
                "critical_alert": (urgency == "EMERGENCY"),
                "next_step": "knowledge" if is_sufficient else "end" # If incomplete, maybe ask more? 
                # For this flow, let's assume if incomplete we might loop or end. 
                # To keep it simple for now: if sufficient -> knowledge, else -> return question
            }
        except Exception as e:
            logger.error(f"Triage error: {e}")
            return {
                "patient_info": {"status": "error", "summary": str(e)},
                "next_step": "end"
            }
