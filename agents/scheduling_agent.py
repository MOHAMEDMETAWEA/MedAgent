"""
Generic Scheduling Agent - No hard-coded providers or hospitals.
Works globally for any healthcare system.
"""
from .state import AgentState
from utils.provider_manager import provider_manager, Specialty
from utils.safety import detect_critical_symptoms

class SchedulingAgent:
    """
    Priority-Aware Scheduling Agent - Generic and Global.
    Uses provider manager to avoid hard-coded dependencies.
    """
    def process(self, state: AgentState):
        print("--- SCHEDULING AGENT: PRIORITIZING CASE ---")
        is_emergency = state.get('critical_alert', False)
        diagnosis = state.get('preliminary_diagnosis', '')
        patient_summary = state.get('patient_info', {}).get('summary', '')
        
        # Enhanced emergency detection
        if not is_emergency:
            is_critical, _ = detect_critical_symptoms(patient_summary + " " + diagnosis)
            is_emergency = is_critical
        
        # Determine specialty using generic provider manager
        specialty = provider_manager.determine_specialty_from_diagnosis(diagnosis)
        
        # Get appointment details from provider manager
        appointment_info = provider_manager.get_appointment_details(
            specialty=specialty,
            is_emergency=is_emergency,
            diagnosis=diagnosis
        )
        
        # Format appointment details
        details = (
            f"### APPOINTMENT INFORMATION ###\n"
            f"Priority: {appointment_info['priority']}\n"
            f"Recommended Specialty: {specialty.value.replace('_', ' ').title()}\n"
            f"Provider Type: {appointment_info['provider']}\n"
            f"Timing: {appointment_info['timing']}\n"
            f"Instructions: {appointment_info['instructions']}\n"
            f"\nNote: This is a generic recommendation. Please consult with your local healthcare provider."
        )
        
        return {
            "appointment_details": details,
            "next_step": "doctor_review"
        }
