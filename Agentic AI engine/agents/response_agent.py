"""
Response Agent - Adaptive Polish
Optimized for performance with lazy imports.
"""

import logging

logger = logging.getLogger(__name__)


class ResponseAgent:
    def __init__(self, model=None):
        from config import settings

        self.model = model or settings.OPENAI_MODEL
        self.temperature = settings.LLM_TEMPERATURE_PATIENT

    def _get_llm(self, state: dict):
        from models.model_router import get_model

        model = state.get("model_used") or self.model
        return get_model(model_name=model, temperature=self.temperature)

    def process(self, state: dict):
        """Final polish of the system response for the user based on Interaction Mode."""
        from langchain_core.messages import HumanMessage, SystemMessage

        from config import get_prompt_path

        logger.info("--- RESPONSE AGENT: ADAPTIVE POLISH ---")
        final_response = state.get("final_response", "")
        if not final_response:
            final_response = state.get("preliminary_diagnosis", "")

        mode = state.get("interaction_mode", "patient")
        role = state.get("user_role", "patient")
        verified = state.get("doctor_verified", False)
        lang = state.get("language", "en")

        if not final_response:
            return state

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
            template_path = get_prompt_path("clinical_communication_layer.txt")
            with open(template_path, "r", encoding="utf-8") as f:
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
                input_content=final_response,
            )
        except Exception as e:
            logger.error(f"Failed to load communication template: {e}")
            prompt = final_response

        try:
            llm = self._get_llm(state)
            response = llm.invoke(
                [
                    SystemMessage(
                        content=f"You are a medical communication expert. Respond in {'Arabic' if lang == 'ar' else 'English'}."
                    ),
                    HumanMessage(content=prompt),
                ]
            )
            adapted_response = response.content

            # Phase 3: Patient Communication Adapter Polish
            if mode == "patient" or role == "patient":
                try:
                    from .patient_adapter import PatientCommunicationAdapter

                    adapter = PatientCommunicationAdapter()
                    adapted_response = adapter.transform(adapted_response, state)
                except Exception as ex:
                    logger.error(f"Patient adapter failed: {ex}")

            state["final_response"] = adapted_response
        except Exception as e:
            logger.error(f"Response adaptation failed: {e}")

        return state
