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
        print("--- RESPONSE AGENT: ADAPTIVE POLISH ---")
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

        prompt = f"""
        Role: Communication Adaptation Specialist.
        Target Audience: {mode.upper()} ({role.upper()})
        Interaction Mode: {mode_label}
        Language: {lang}

        INPUT CONTENT:
        {final_response}

        TASK:
        Rewrite the input content to perfectly suit the Target Audience.
        
        IF MODE IS PATIENT:
        - Use simple language and easy explanations.
        - Avoid technical jargon (or explain it simply).
        - Use examples and provide reassurance.
        - Focus on understanding and guidance.
        
        IF MODE IS DOCTOR:
        - Use advanced medical terminology.
        - Detailed reasoning and differential diagnosis.
        - Clinical explanation and evidence-based analysis.
        - Maintain technical precision.

        Retain the core medical meaning exactly. Do not change the diagnosis or safety advice.
        """

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
