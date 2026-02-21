from typing import TypedDict, List, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the multi-agent system.
    """
    # Messaging history
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Context
    user_id: str
    session_id: str
    
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

    # Layer 1 — Identity & Role Context
    interaction_mode: str      # 'doctor' or 'patient'
    user_role: str             # 'doctor' or 'patient'
    doctor_verified: bool
    user_age: str
    user_gender: str
    user_country: str
    request_second_opinion: bool
    
    # Generative Report Agent outputs (RAG-grounded) - Compatibility
    report_medical: str
    report_doctor_summary: str
    report_patient_instructions: str
    
    # Transparency
    status: str # Descriptive status for UI
    
    # Multimodal Vision Integration
    image_path: str # Local path or URL to uploaded image
    visual_findings: dict # Output from Vision Analysis Agent

    # Advanced Memory & Tracking
    long_term_memory: str # Summarized past history/conversations
    conversation_state: dict # Active case tracking (risk_level, pending_actions, etc.)