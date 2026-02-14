"""
Patient Agent with Enhanced Input Validation and Global Support.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import sanitize_input, validate_medical_input, detect_prompt_injection
import logging

logger = logging.getLogger(__name__)

class PatientAgent:
    """
    Inquisitive Patient Agent that ensures high-quality input for the diagnosis engine.
    Enhanced with safety checks and global usability.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_PATIENT,
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
        print("--- PATIENT AGENT: VALIDATING INTAKE ---")
        messages = state.get('messages', [])
        
        if not messages:
            return {
                "patient_info": {
                    "summary": "No patient input provided. Please describe your symptoms.",
                    "status": "incomplete"
                },
                "next_step": "diagnosis"
            }
        
        # Extract and validate user input
        user_input = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                user_input += str(msg.content) + " "
        
        # Sanitize and validate input
        user_input = sanitize_input(user_input)
        is_valid, error_msg = validate_medical_input(user_input)
        
        if not is_valid:
            return {
                "patient_info": {
                    "summary": f"Input validation failed: {error_msg}. Please provide valid symptom information.",
                    "status": "error"
                },
                "next_step": "diagnosis"
            }
        
        # Check for prompt injection
        is_injection, patterns = detect_prompt_injection(user_input)
        if is_injection:
            logger.warning(f"Potential prompt injection detected: {patterns}")
            # Continue but log the issue
        
        # Load prompt template
        prompt_template = self._load_prompt('patient_agent.txt')
        if not prompt_template:
            return {
                "patient_info": {
                    "summary": "System configuration error. Please contact support.",
                    "status": "error"
                },
                "next_step": "diagnosis"
            }
        
        try:
            system_msg = SystemMessage(content=prompt_template)
            response = self.llm.invoke([system_msg] + list(messages))
            
            is_sufficient = "PATIENT SUMMARY:" in response.content
            
            return {
                "patient_info": {
                    "summary": response.content, 
                    "status": "complete" if is_sufficient else "incomplete"
                },
                "next_step": "diagnosis"
            }
        except Exception as e:
            logger.error(f"Error in patient agent: {e}")
            return {
                "patient_info": {
                    "summary": f"Error processing patient intake: {str(e)}. Please try again.",
                    "status": "error"
                },
                "next_step": "diagnosis"
            }
