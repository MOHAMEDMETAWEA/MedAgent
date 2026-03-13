from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings
import logging

logger = logging.getLogger(__name__)

class ResponseAgent:
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=settings.LLM_TEMPERATURE_PATIENT,
            api_key=settings.OPENAI_API_KEY
        )

    def process(self, state: AgentState):
        """Final polish of the system response for the user based on Interaction Mode."""
        logger.info("--- RESPONSE AGENT: ADAPTIVE POLISH ---")
        final_response = state.get("final_response", "")
        mode = state.get("interaction_mode", "patient")
        role = state.get("user_role", "patient")
        verified = state.get("doctor_verified", False)
        lang = state.get("language", "en")
        
        if not final_response:
             return state

        # If not verified doctor, add a badge/tag to the mode
        mode_label = mode.upper()
        if mode == "doctor" and not verified:
            mode_label = "UNVERIFIED DOCTOR MODE"
            
        edu = state.get("education_level", "unknown")
        lit = state.get("medical_literacy_level", "moderate")
        emo = state.get("emotional_state", "calm")
        age = state.get("user_age", "Unknown")
        gender = state.get("user_gender", "Unknown")
        country = state.get("user_country", "Unknown")

        try:
            from config import get_prompt_path
            template_path = get_prompt_path("clinical_communication_layer.txt")
            with open(template_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()

            prompt = base_prompt.format(
                mode=mode_label,
                role=role.upper(),
                verified=str(verified),
                age=age,
                gender=gender,
                country=country,
                education=edu.upper(),
                literacy=lit.upper(),
                emotion=emo.upper(),
                input_content=final_response
            )
        except Exception as e:
            logger.error(f"Failed to load communication template: {e}")
            prompt = final_response # Fallback

        try:
            response = self.llm.invoke([
                SystemMessage(content=f"You are a medical communication expert. Respond in {'Arabic' if lang == 'ar' else 'English'}."),
                HumanMessage(content=prompt)
            ])
            state["final_response"] = response.content
        except Exception as e:
            logger.error(f"Response adaptation failed: {e}")
            # Fallback to original
            pass

        return state
