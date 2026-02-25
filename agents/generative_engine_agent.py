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
        """Generate educational article or summary using Registry."""
        from agents.prompts.registry import PROMPT_REGISTRY
        entry = PROMPT_REGISTRY.get("MED-GEN-EDU-001")
        if not entry: return "Education prompt missing."
        
        try:
            is_injection, _ = detect_prompt_injection(topic)
            if is_injection: return "Error: unsafe topic request."
            
            prompt = entry.content.format(topic=topic, audience_level=audience_level, lang=lang)
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Education Specialist. Provide accurate, safe, and clear information."),
                HumanMessage(content=prompt)
            ])
            return add_safety_disclaimer(response.content)
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating content."

    def generate_simulation_scenario(self, condition: str, difficulty: str = "medium") -> str:
        """Generate a clinical case scenario using Registry."""
        from agents.prompts.registry import PROMPT_REGISTRY
        entry = PROMPT_REGISTRY.get("MED-GEN-SIM-001")
        if not entry: return "Simulation prompt missing."
        
        try:
            prompt = entry.content.format(condition=condition, difficulty=difficulty)
            response = self.llm.invoke([
                SystemMessage(content="You are a Clinical Simulation Expert. valuable for medical training."), 
                HumanMessage(content=prompt)
            ])
            return response.content
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating simulation."

    def generate_personalized_plan(self, patient_profile: dict, diagnosis: str) -> str:
        """Create a personalized care plan using Registry."""
        from agents.prompts.registry import PROMPT_REGISTRY
        entry = PROMPT_REGISTRY.get("MED-GEN-PLAN-001")
        if not entry: return "Care plan prompt missing."
        
        summary = f"Age: {patient_profile.get('age')}, Gender: {patient_profile.get('gender')}. Region: {patient_profile.get('country')}"
        
        try:
            prompt = entry.content.format(diagnosis=diagnosis, profile_summary=summary)
            response = self.llm.invoke([
                SystemMessage(content="You are a Personalized Care Specialist. Output actionable, safe lifestyle advice."),
                HumanMessage(content=prompt)
            ])
            return add_safety_disclaimer(response.content)
        except Exception as e:
            logger.error(f"Gen Engine Error: {e}")
            return "Error generating plan."
