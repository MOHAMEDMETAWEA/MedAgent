"""
Multi-Agent Orchestrator - Global Generic Architecture.
Optimized for performance with lazy agent loading.
"""
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langdetect import detect
from .state import AgentState
from config import settings
from utils.safety import sanitize_input, validate_medical_input
import logging

logger = logging.getLogger(__name__)

class MedAgentOrchestrator:
    def __init__(self):
        try:
            self._agents = {}
            self.graph = self._build_graph()
            logger.info("Orchestrator Initialized (Lazy Loading Enabled)")
        except Exception as e:
            logger.error(f"Error initializing orchestrator: {e}")
            raise

    def get_agent(self, name):
        """Lazy loader for internal agents."""
        if name in self._agents:
            return self._agents[name]
        
        # Explicit lazy mappings (Safest)
        if name == "patient":
            from .patient_agent import PatientAgent
            self._agents[name] = PatientAgent()
        elif name == "triage":
            from .triage_agent import TriageAgent
            self._agents[name] = TriageAgent()
        elif name == "knowledge":
            from .knowledge_agent import KnowledgeAgent
            self._agents[name] = KnowledgeAgent()
        elif name == "reasoning":
            from .reasoning_agent import ReasoningAgent
            self._agents[name] = ReasoningAgent()
        elif name == "validation":
            from .validation_agent import ValidationAgent
            self._agents[name] = ValidationAgent()
        elif name == "safety":
            from .safety_agent import SafetyAgent
            self._agents[name] = SafetyAgent()
        elif name == "response":
            from .response_agent import ResponseAgent
            self._agents[name] = ResponseAgent()
        elif name == "persistence":
            from .persistence_agent import PersistenceAgent
            self._agents[name] = PersistenceAgent()
        elif name == "supervisor":
            from .supervisor_agent import SupervisorAgent
            self._agents[name] = SupervisorAgent()
        elif name == "vision":
            from .vision_agent import VisionAnalysisAgent
            self._agents[name] = VisionAnalysisAgent()
        elif name == "diagnosis":
            from .diagnosis_agent import DiagnosisAgent
            self._agents[name] = DiagnosisAgent()
        elif name == "report":
            from .report_agent import ReportAgent
            self._agents[name] = ReportAgent()
        # Add any others that are used in the graph or run()
        return self._agents.get(name)

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        def wrap_node(node_name):
            def wrapper(state: AgentState):
                logger.info(f"--- AGENT: {node_name.upper()} ---")
                agent = self.get_agent(node_name)
                if not agent:
                    logger.error(f"Agent {node_name} not found!")
                    return state
                return agent.process(state)
            return wrapper

        workflow.add_node("vision", wrap_node("vision"))
        workflow.add_node("patient", wrap_node("patient"))
        workflow.add_node("triage", wrap_node("triage"))
        workflow.add_node("knowledge", wrap_node("knowledge"))
        workflow.add_node("reasoning", wrap_node("reasoning"))
        workflow.add_node("validation", wrap_node("validation"))
        workflow.add_node("safety", wrap_node("safety"))
        workflow.add_node("response", wrap_node("response"))

        # Conditional Entry: If image exists, start with vision, else patient
        def route_start(state: AgentState):
            if state.get("image_path"):
                return "vision"
            return "patient"

        workflow.set_conditional_entry_point(
            route_start,
            {
                "vision": "vision",
                "patient": "patient"
            }
        )

        workflow.add_edge("vision", "patient")
        workflow.add_edge("patient", "triage")
        workflow.add_edge("triage", "knowledge")
        workflow.add_edge("knowledge", "reasoning")
        workflow.add_edge("reasoning", "validation")
        workflow.add_edge("validation", "safety")
        workflow.add_edge("safety", "response")
        workflow.add_edge("response", END)

        return workflow.compile()

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return "ar" if lang == "ar" else "en"
        except:
            return "en"

    def run(self, initial_input: str, user_id: str = "guest", image_path: str = None, request_second_opinion: bool = False, interaction_mode: str = None):
        persistence = self.get_agent("persistence")
        sanitized = sanitize_input(initial_input)
        is_valid, error_msg = validate_medical_input(sanitized)
        if not is_valid:
            return {"final_response": f"Input validation failed: {error_msg}.", "status": "error"}
        
        user_profile = {}
        if user_id != "guest":
            from database.models import UserAccount, PatientProfile
            db = persistence._get_db()
            try:
                user_acc = db.query(UserAccount).filter(UserAccount.id == user_id).first()
                if user_acc:
                    user_profile = {
                        "role": user_acc.role if hasattr(user_acc.role, 'value') else user_acc.role,
                        "gender": user_acc.gender,
                        "age": user_acc.age,
                        "country": user_acc.country,
                        "interaction_mode": user_acc.interaction_mode,
                        "doctor_verified": user_acc.doctor_verified
                    }
                    patient_p = db.query(PatientProfile).filter(PatientProfile.id == user_id).first()
                    if patient_p and patient_p.medical_history_encrypted:
                        user_profile["medical_background"] = patient_p.medical_history_encrypted
            finally:
                db.close()
        
        final_mode = interaction_mode or user_profile.get("interaction_mode", "patient")
        session_id = persistence.create_session(user_id=user_id, mode=final_mode)
        lang = self.detect_language(sanitized)
        
        try:
            state = {
                "messages": [HumanMessage(content=sanitized)],
                "user_id": user_id,
                "session_id": session_id,
                "patient_info": {},
                "preliminary_diagnosis": "",
                "retrieved_docs": "",
                "doctor_notes": "",
                "validation_status": "",
                "safety_status": "",
                "final_response": "",
                "critical_alert": False,
                "language": lang,
                "interaction_mode": final_mode,
                "user_role": user_profile.get("role", "patient"),
                "doctor_verified": user_profile.get("doctor_verified", False),
                "user_age": user_profile.get("age"),
                "user_gender": user_profile.get("gender"),
                "user_country": user_profile.get("country"),
                "requires_human_review": False,
                "status": "Processing...",
                "image_path": image_path,
                "request_second_opinion": request_second_opinion,
                "visual_findings": {},
                "long_term_memory": user_profile.get("medical_background", ""),
                "medical_background": user_profile.get("medical_background", ""),
                "conversation_state": {"active_case_id": None, "risk_level": "unknown", "pending_actions": []}
            }
            
            final_state = self.graph.invoke(state)
            
            persistence.save_interaction(
                session_id=session_id,
                user_input=sanitized,
                result=final_state
            )
            
            return final_state
        except Exception as e:
            logger.error(f"Orchestrator run error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"final_response": "The system encountered a critical error. Please try again.", "status": "error"}
