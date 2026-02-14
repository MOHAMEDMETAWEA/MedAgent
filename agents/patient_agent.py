"""
Patient Agent with Enhanced Input Validation and Global Support.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
from utils.safety import sanitize_input, validate_medical_input, detect_prompt_injection
from agents.persistence_agent import PersistenceAgent
import logging
import json

logger = logging.getLogger(__name__)

class PatientAgent:
    """
    Patient Agent: Personalized Assistant & Intake Manager.
    - Loads patient profile/history from persistence.
    - Validates new symptom input.
    - Updates context for downstream agents.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_PATIENT,
            api_key=settings.OPENAI_API_KEY
        )
        self.persistence = PersistenceAgent()

    def _load_prompt(self, filename: str) -> str:
        try:
            prompt_path = get_prompt_path(filename)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""

    def process(self, state: AgentState):
        print("--- PATIENT AGENT: LOADING PROFILE & VALIDATING INTAKE ---")
        
        user_id = state.get('user_id', 'GUEST')
        messages = state.get('messages', [])
        
        # 1. Load Profile
        profile = self.persistence.get_patient_profile(user_id)
        history_context = ""
        if profile:
            history_context = f"Patient Name: {profile.get('name')}, Age: {profile.get('age')}, History: {profile.get('medical_history')}"
        else:
            history_context = "New Patient (Guest)"
            # Auto-create guest profile if needed, or wait for explicit registration
        
        if not messages:
            return {
                "patient_info": {
                    "summary": "No patient input provided.",
                    "status": "incomplete",
                    "history": history_context
                },
                "next_step": "triage" # Determine next step
            }
        
        # 2. Extract and Validate Input
        user_input = messages[-1].content if messages else ""
        
        user_input = sanitize_input(user_input)
        is_valid, error_msg = validate_medical_input(user_input)
        
        if not is_valid:
            return {
                "patient_info": {
                    "summary": f"Input validation failed: {error_msg}.",
                    "status": "error",
                    "history": history_context
                },
                "next_step": "end"
            }
        
        # 3. Contextual Analysis (LLM)
        # We use strict prompt to summarize symptoms, now including history context
        prompt_template = self._load_prompt('patient_agent.txt')
        if not prompt_template:
             # Fallback
             prompt_template = "Summarize the patient symptoms from the following input: {input}\nContext: {context}"
             
        full_prompt = f"Patient History Context: {history_context}\n\n" + prompt_template
        
        try:
            system_msg = SystemMessage(content=full_prompt)
            # Pass only the last message to avoid context window bloat, 
            # or pass all if this is a conversation. System uses single-turn usually.
            response = self.llm.invoke([system_msg, HumanMessage(content=user_input)])
            
            is_sufficient = "PATIENT SUMMARY:" in response.content
            
            # If profile existed, we might update it? 
            # For now, we just pass the info downstream.
            
            return {
                "patient_info": {
                    "summary": response.content, 
                    "status": "complete" if is_sufficient else "incomplete",
                    "history_context": history_context,
                    "profile_id": user_id
                },
                "next_step": "triage" 
            }
        except Exception as e:
            logger.error(f"Error in patient agent: {e}")
            return {
                "patient_info": {"status": "error", "summary": str(e)},
                "next_step": "end"
            }
