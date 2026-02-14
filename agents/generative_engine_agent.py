"""
Generative Engine Agent – Dynamic Content Creation.
Generates: Educational Content, Personalized Recommendations, Simulations, Analytics Summaries.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings
from utils.safety import add_safety_disclaimer, detect_prompt_injection
import logging
import json

logger = logging.getLogger(__name__)

class GenerativeEngineAgent:
    """
    Versatile Generative Engine for dynamic medical content.
    - Educational Materials
    - Scenario Simulations
    - Personalized Care Plans
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model,
            temperature=settings.LLM_TEMPERATURE_REASONING, # Creative but grounded
            api_key=settings.OPENAI_API_KEY
        )

    def generate_educational_content(self, topic: str, audience_level: str = "patient", lang: str = "en") -> str:
        """Generate educational article or summary."""
        prompt = f"Create a short educational medical summary about '{topic}' for a {audience_level} audience. Language: {lang}. Ensure accuracy and clarity."
        
        try:
            # Check for injection in topic
            is_injection, _ = detect_prompt_injection(topic)
            if is_injection:
                 return "Error: unsafe topic request."
            
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Education Specialist. Provide accurate, safe, and clear information."),
                HumanMessage(content=prompt)
            ])
            return add_safety_disclaimer(response.content)
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating content."

    def generate_simulation_scenario(self, condition: str, difficulty: str = "medium") -> str:
        """Generate a clinical case scenario for training."""
        prompt = f"Generate a realistic clinical case scenario for a patient with {condition}. Difficulty: {difficulty}. Include: Patient Profile, Chief Complaint, Vitals, and History."
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Clinical Simulation Expert. valuable for medical training."), 
                HumanMessage(content=prompt)
            ])
            return response.content
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating simulation."

    def generate_personalized_plan(self, patient_profile: dict, diagnosis: str) -> str:
        """Create a personalized care plan based on profile and diagnosis."""
        # This would use RAG in a full implementation
        summary = f"Patient: {patient_profile.get('age')}yo {patient_profile.get('gender')}. History: {patient_profile.get('medical_history')}. Diagnosis: {diagnosis}"
        prompt = f"Create a personalized care plan (diet, lifestyle, monitoring) for: {summary}"
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Personalized Care Specialist. Output actionable, safe lifestyle advice."),
                HumanMessage(content=prompt)
            ])
            return add_safety_disclaimer(response.content)
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating plan."
