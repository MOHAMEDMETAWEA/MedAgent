"""
Doctor Agent with Enhanced Safety and Global Medical Standards.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import add_safety_disclaimer
import logging

logger = logging.getLogger(__name__)

class DoctorAgent:
    """
    Expert Validation Agent that produces standardized SOAP medical reports.
    Enhanced with safety checks and global medical standards.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_DOCTOR,
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename: str) -> str:
        """Load prompt file using configurable path."""
        try:
            prompt_path = get_prompt_path(filename)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filename}")
            return ""
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def process(self, state: AgentState):
        print("--- DOCTOR AGENT: GENERATING SOAP REPORT ---")
        diagnosis = state.get('preliminary_diagnosis', '')
        patient_summary = state.get('patient_info', {}).get('summary', '')
        
        if not diagnosis and not patient_summary:
            return {
                "doctor_notes": "Insufficient information to generate medical report. Please provide patient symptoms.",
                "next_step": "end"
            }
        
        prompt_template = self._load_prompt('doctor_agent.txt')
        if not prompt_template:
            return {
                "doctor_notes": "System configuration error. Please contact support.",
                "next_step": "end"
            }
        
        try:
            system_msg = SystemMessage(content=prompt_template)
            
            prompt = (
                f"PRELIMINARY AI DATA:\n{diagnosis}\n\n"
                f"PATIENT INTAKE DATA:\n{patient_summary}\n\n"
                f"IMPORTANT: This is an AI-generated report for educational purposes only. "
                f"Always express uncertainty when appropriate and emphasize the need for professional medical consultation."
            )
            
            response = self.llm.invoke([system_msg, SystemMessage(content=prompt)])
            
            # Add safety disclaimer
            notes_with_disclaimer = add_safety_disclaimer(response.content)
            
            return {
                "doctor_notes": notes_with_disclaimer,
                "next_step": "end"
            }
        except Exception as e:
            logger.error(f"Error in doctor agent: {e}")
            return {
                "doctor_notes": f"Error generating medical report: {str(e)}. Please consult a healthcare professional.",
                "next_step": "end"
            }
