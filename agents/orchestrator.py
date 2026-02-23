"""
Multi-Agent Orchestrator - Global Generic Architecture.
Workflow: Triage -> Knowledge -> Reasoning -> Validation -> Safety -> Response.
Now supports: Bilingual (AR/EN), Persistence, and Human Review flagging.
"""
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langdetect import detect
from .state import AgentState
from .triage_agent import TriageAgent
from .knowledge_agent import KnowledgeAgent
from .reasoning_agent import ReasoningAgent
from .validation_agent import ValidationAgent
from .safety_agent import SafetyAgent
from .report_agent import ReportAgent
from .response_agent import ResponseAgent
from .doctor_agent import DoctorAgent
from .diagnosis_agent import DiagnosisAgent
from .scheduling_agent import SchedulingAgent
from .patient_agent import PatientAgent
from .vision_agent import VisionAnalysisAgent
from .calendar_agent import CalendarAgent
from .persistence_agent import PersistenceAgent
from .supervisor_agent import SupervisorAgent 
from .self_improvement_agent import SelfImprovementAgent 
from .human_review_agent import HumanReviewAgent
from .authentication_agent import AuthenticationAgent
from .medication_agent import MedicationAgent
from .second_opinion_agent import SecondOpinionAgent
from config import settings
from utils.safety import sanitize_input, validate_medical_input
import logging

logger = logging.getLogger(__name__)

class MedAgentOrchestrator:
    def __init__(self):
        try:
            self.patient_agent = PatientAgent()
            self.triage_agent = TriageAgent()
            self.knowledge_agent = KnowledgeAgent()
            self.reasoning_agent = ReasoningAgent()
            self.validation_agent = ValidationAgent()
            self.safety_agent = SafetyAgent()
            self.report_agent = ReportAgent() 
            self.response_agent = ResponseAgent()
            self.doctor_agent = DoctorAgent()
            self.diagnosis_agent = DiagnosisAgent()
            self.scheduling_agent = SchedulingAgent()
            self.vision_agent = VisionAnalysisAgent()
            self.calendar_agent = CalendarAgent()
            self.persistence = PersistenceAgent()
            self.supervisor = SupervisorAgent()
            self.improver = SelfImprovementAgent()
            self.reviewer_agent = HumanReviewAgent()
            self.auth_agent = AuthenticationAgent()
            self.medication_agent = MedicationAgent()
            self.second_opinion_agent = SecondOpinionAgent()
            
            self.graph = self._build_graph()
            
            # Start Up Health Check
            self.supervisor.log_event("STARTUP", "System Initialized")
        except Exception as e:
            logger.error(f"Error initializing orchestrator: {e}")
            raise

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Wrapper functions for transparency
        def wrap_node(node_name, agent_func):
            def wrapper(state: AgentState):
                state["status"] = f"Agent: {node_name.capitalize()} is processing..."
                self.persistence.log_system_event("INFO", "Orchestrator", f"Transition to {node_name}", session_id=state.get("session_id"))
                return agent_func(state)
            return wrapper

        workflow.add_node("patient", wrap_node("patient", self.patient_agent.process))
        workflow.add_node("triage", wrap_node("triage", self.triage_agent.process))
        workflow.add_node("knowledge", wrap_node("knowledge", self.knowledge_agent.process))
        workflow.add_node("reasoning", wrap_node("reasoning", self.reasoning_agent.process))
        workflow.add_node("validation", wrap_node("validation", self.validation_agent.process))
        workflow.add_node("report", wrap_node("report", self.report_agent.process))
        workflow.add_node("response", wrap_node("response", self.response_agent.process))
        workflow.add_node("doctor", wrap_node("doctor", self.doctor_agent.process))
        workflow.add_node("diagnosis", wrap_node("diagnosis", self.diagnosis_agent.process))
        workflow.add_node("scheduling", wrap_node("scheduling", self.scheduling_agent.process))
        workflow.add_node("calendar", wrap_node("calendar", self.calendar_agent.process))
        workflow.add_node("vision", wrap_node("vision", self.vision_agent.process))
        workflow.add_node("medication", wrap_node("medication", self.medication_agent.process))
        workflow.add_node("second_opinion", wrap_node("second_opinion", self.second_opinion_agent.process))
        workflow.add_node("safety", wrap_node("safety", self.safety_agent.process))

        # Entry Point is now Patient Agent to load Context
        workflow.set_entry_point("patient")
        
        # Route logic after Patient Agent (which provides context and basic pass-through)
        def route_intent(state):
            user_input = state.get('messages', [])[-1].content.lower()
            if state.get("image_path"):
                return "vision"
            if "book" in user_input or "schedule" in user_input or "appointment" in user_input or "احجز" in user_input or "موعد" in user_input:
                return "scheduling"
            if any(kw in user_input for kw in ["medication", "medicine", "pill", "dose", "drug", "دواء", "حبوب", "جرعة"]):
                return "medication"
            return "triage"

        # Conditional Edge after Patient loading
        workflow.add_conditional_edges("patient", route_intent, {
            "triage": "triage", 
            "scheduling": "scheduling", 
            "vision": "vision",
            "medication": "medication"
        })
        
        workflow.add_edge("vision", "triage") 
        
        # Conditional Edge after Triage: if insufficient docs -> knowledge -> reasoning, elser -> END or LOOP
        # For simplicity in this launch, we follow the best-case path but with safety.
        workflow.add_edge("triage", "knowledge")
        workflow.add_edge("knowledge", "diagnosis")
        workflow.add_edge("diagnosis", "reasoning")
        workflow.add_edge("reasoning", "validation")
        workflow.add_edge("validation", "doctor")
        workflow.add_edge("doctor", "safety")
        workflow.add_edge("safety", "second_opinion")
        workflow.add_edge("second_opinion", "report")
        workflow.add_edge("report", "response")
        workflow.add_edge("response", END)
        workflow.add_edge("scheduling", "calendar")
        workflow.add_edge("calendar", END)
        workflow.add_edge("medication", END)

        return workflow.compile()

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return "ar" if lang == "ar" else "en"
        except:
            return "en"

    def run(self, initial_input: str, user_id: str = "guest", image_path: str = None, request_second_opinion: bool = False, interaction_mode: str = None):
        # 1. Validation & Persistence Setup
        is_valid, error_msg = validate_medical_input(sanitize_input(initial_input))
        if not is_valid:
            self.persistence.log_system_event("WARNING", "Orchestrator", "Invalid Input", {"error": error_msg})
            self.supervisor.log_event("WARNING", f"Invalid Input: {error_msg}")
            return {"final_response": f"Input validation failed: {error_msg}. Please try again.", "status": "error"}
        
        sanitized_input = sanitize_input(initial_input)
        
        # 2. Fetch User Profile for Role-Aware Reasoning
        user_profile = {}
        if user_id != "guest":
            # Direct query to get full account details including role
            from database.models import UserAccount
            user_acc = self.persistence.db.query(UserAccount).filter(UserAccount.id == user_id).first()
            if user_acc:
                user_profile = {
                    "role": user_acc.role,
                    "gender": user_acc.gender,
                    "age": user_acc.age,
                    "country": user_acc.country,
                    "interaction_mode": user_acc.interaction_mode,
                    "doctor_verified": user_acc.doctor_verified
                }
        
        # Default mode logic
        final_mode = interaction_mode or user_profile.get("interaction_mode", "patient")
        session_id = self.persistence.create_session(user_id=user_id, mode=final_mode)
        
        # 3. Language Detection
        lang = self.detect_language(sanitized_input)
        
        try:
            state = {
                "messages": [HumanMessage(content=sanitized_input)],
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
                # New Fields
                "language": lang,
                "interaction_mode": final_mode,
                "user_role": user_profile.get("role", "patient"),
                "doctor_verified": user_profile.get("doctor_verified", False),
                "user_age": user_profile.get("age"),
                "user_gender": user_profile.get("gender"),
                "user_country": user_profile.get("country"),
                "requires_human_review": False,
                "status": "Initializing...",
                "image_path": image_path,
                "request_second_opinion": request_second_opinion,
                "visual_findings": {},
                "long_term_memory": "",
                "conversation_state": {"active_case_id": None, "risk_level": "unknown", "pending_actions": []}
            }
            
            result = self.graph.invoke(state)
            
            # 3. Post-Process for Human Review Flagging
            needs_review = result.get('critical_alert', False) or result.get('validation_status') == 'warning'
            
            result['requires_human_review'] = needs_review
            result['language'] = lang
            
            # Save interaction with CASE linking
            case_id = result.get("conversation_state", {}).get("active_case_id")
            if not case_id and user_id != "guest":
                case_id = self.persistence.get_or_create_case(user_id, title=sanitized_input[:50])
                if "conversation_state" not in result: result["conversation_state"] = {}
                result["conversation_state"]["active_case_id"] = case_id

            self.persistence.save_interaction(session_id, sanitized_input, result, case_id=case_id)
            
            # Save visual findings if exists
            if image_path and result.get("visual_findings"):
                self.persistence.save_medical_image(
                    session_id, 
                    image_path, 
                    result["visual_findings"], 
                    patient_id=user_id if user_id != "guest" else None,
                    case_id=case_id
                )
            
            self.persistence.log_system_event("INFO", "Orchestrator", "Consultation Complete", {"session_id": session_id, "lang": lang})

            if self.improver:
                 self.improver.analyze_feedback() 
            
            # 5. USER COMFORT OPTIMIZATION
            result = self._optimize_user_comfort(result)
            return result
        except Exception as e:
            logger.error(f"Error in orchestrator run: {e}")
            self.persistence.log_system_event("ERROR", "Orchestrator", f"Runtime Error: {e}", session_id=session_id)
            self.supervisor.log_event("ERROR", f"Orchestrator Crashed: {e}")
            return {"final_response": f"System error: {str(e)}.", "status": "error"}

    def _optimize_user_comfort(self, result: dict) -> dict:
        """Section 4: User Comfort and UX Optimization Authority Implementation."""
        lang = result.get("language", "en")
        
        # Clear & Simple Message Guarantee
        if result.get("critical_alert"):
            alert_msg = "🚨 URGENT: Our analysis indicates high risk. Please go to the nearest emergency room immediately." if lang == "en" else "🚨 عاجل: يشير تحليلنا إلى وجود مخاطر عالية. يرجى التوجه إلى أقرب غرفة طوارئ على الفور."
            result["final_response"] = f"{alert_msg}\n\n{result.get('final_response', '')}"
        
        # Workflow Guidance
        guidance = "\n\n**Next Suggested Step:** You can now generate a formal report or book a follow-up in the tabs above." if lang == "en" else "\n\n**الخطوة التالية المقترحة:** يمكنك الآن إنشاء تقرير رسمي أو حجز موعد متابعة من علامات التبويب أعلاه."
        result["final_response"] += guidance
        
        # Clear system action transparency
        result["status"] = "Ready / النظام جاهز للمساعدة" if lang == "ar" else "System Ready to Assist"
        
        return result
