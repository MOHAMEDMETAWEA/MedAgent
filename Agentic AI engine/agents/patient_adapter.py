import logging

from utils.medical_terms import explain_text

from .state import AgentState

logger = logging.getLogger(__name__)


class PatientCommunicationAdapter:
    """
    Transforms clinical outputs into patient-friendly explanations.
    """

    def transform(self, clinical_output: str, state: AgentState) -> str:
        """
        Main entry point for transformation.
        """
        lit = state.get("medical_literacy_level", "moderate") or "moderate"
        age = state.get("user_age", 30)

        # Use full replacement for low literacy or elderly (Age > 70)
        replace_only = (lit.lower() == "low") or (isinstance(age, int) and age > 70)

        simplified = explain_text(clinical_output, replace_only=replace_only)

        # 2. Safety Layer (Phase 6)
        # Ensure emergency detection is prominent
        is_emergency = (
            state.get("critical_alert", False) or state.get("risk_level") == "emergency"
        )
        if is_emergency:
            emergency_warning = "\n\n> [!CAUTION]\n> **EMERGENCY WARNING**: Based on your symptoms, we detected signals that may require immediate medical attention. Please seek emergency care right away."
            if "emergency" not in simplified.lower():
                simplified = emergency_warning + "\n\n" + simplified
        elif "doctor" not in simplified.lower():
            simplified += "\n\n*Note: This analysis is for guidance only. If your symptoms worsen, please consult a doctor.*"

        # 3. Education & Personalization (Phase 7 & 9)
        # Add a placeholder for education if specific blocks are missing
        if "next steps" not in simplified.lower() and "do" not in simplified.lower():
            age = state.get("user_age", 30)
            if isinstance(age, int) and age > 60:
                simplified += "\n\n**Health Tip**: As we age, monitoring symptoms closely is important. Ensure you are staying hydrated and following any existing treatment plans."
            elif isinstance(age, int) and age < 16:
                simplified += "\n\n**Note for Parents**: Monitor for high fever or changes in behavior and consult a pediatrician if you have concerns."

        # 4. Interactive Follow-up (Phase 4)
        if "?" not in simplified:
            simplified += "\n\nWould you like me to explain what usually causes these symptoms or how to manage them at home?"

        return simplified
