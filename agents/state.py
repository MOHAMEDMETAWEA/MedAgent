from typing import TypedDict, List, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the multi-agent system.
    """
    # Messaging history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Core Data
    patient_info: dict
    preliminary_diagnosis: str
    retrieved_docs: str
    
    # Agent Outputs
    validation_status: str
    safety_status: str
    doctor_notes: str 
    appointment_details: str
    critical_alert: bool
    next_step: str
    
    # Final Formatted Output
    final_response: str
    
    # Global/Generic & new features
    language: str # 'en' or 'ar'
    requires_human_review: bool
    
    # Generative Report Agent outputs (RAG-grounded) - Compatibility
    report_medical: str
    report_doctor_summary: str
    report_patient_instructions: str