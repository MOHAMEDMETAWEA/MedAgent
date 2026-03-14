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

    def get_agent(self, name: str):
        """Standard mapping of nodes to agent instances."""
        # All agent imports are now centralized here for direct instantiation
        from .patient_agent import PatientAgent
        from .triage_agent import TriageAgent
        from .knowledge_agent import KnowledgeAgent
        from .reasoning_agent import ReasoningAgent
        from .validation_agent import ValidationAgent
        from .safety_agent import SafetyAgent
        from .response_agent import ResponseAgent
        from .persistence_agent import PersistenceAgent
        from .supervisor_agent import SupervisorAgent
        from .vision_agent import VisionAnalysisAgent # Original name was VisionAnalysisAgent
        from .diagnosis_agent import DiagnosisAgent
        from .report_agent import ReportAgent
        from .clinical_review_agent import ClinicalReviewAgent
        from .safety_guardrail_agent import SafetyGuardrailAgent # New agent

        agents_map = {
            "patient": PatientAgent,
            "triage": TriageAgent,
            "knowledge": KnowledgeAgent,
            "reasoning": ReasoningAgent,
            "validation": ValidationAgent,
            "safety": SafetyAgent,
            "response": ResponseAgent,
            "persistence": PersistenceAgent,
            "supervisor": SupervisorAgent,
            "vision": VisionAnalysisAgent, # Map to VisionAnalysisAgent
            "diagnosis": DiagnosisAgent,
            "report": ReportAgent,
            "clinical_review": ClinicalReviewAgent,
            "safety_guardrail": SafetyGuardrailAgent # New mapping
        }
        
        if name in agents_map:
            # Instantiate and return the agent
            if name not in self._agents: # Cache instantiated agents
                self._agents[name] = agents_map[name]()
            return self._agents[name]
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
        elif name == "clinical_review":
            from .clinical_review_agent import ClinicalReviewAgent
            self._agents[name] = ClinicalReviewAgent()
        # Add any others that are used in the graph or run()
        return self._agents.get(name)

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        def wrap_node(node_name):
            def wrapper(state: AgentState):
                agent = self.get_agent(node_name)
                if not agent:
                    logger.error(f"Agent {node_name} not found!")
                    return state
                # Use standardized run() if it exists (BaseAgent), else fallback to process()
                if hasattr(agent, "run"):
                    return agent.run(state)
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
        workflow.add_node("review", wrap_node("clinical_review"))

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

        # Conditional Edge after Triage: Route to Knowledge or Review
        def route_triage(state: AgentState):
            if state.get("risk_level") in ["High", "Emergency"] and not state.get("doctor_verified"):
                return "review"
            return "knowledge"

        workflow.add_conditional_edges(
            "triage",
            route_triage,
            {
                "review": "review",
                "knowledge": "knowledge"
            }
        )

        workflow.add_edge("review", END) # Pause for human review
        workflow.add_edge("knowledge", "reasoning")
        workflow.add_edge("reasoning", "validation")
        
        # Self-Correction Loop: Validation -> Reasoning (if invalid)
        def route_validation(state: AgentState):
            if state.get("validation_status") == "invalid" and state.get("correction_count", 0) < 2:
                logger.warning(f"--- RE-ROUTING TO REASONING (Correction #{state.get('correction_count', 0) + 1}) ---")
                return "retry"
            return "continue"

        workflow.add_conditional_edges(
            "validation",
            route_validation,
            {
                "retry": "reasoning",
                "continue": "safety"
            }
        )

        workflow.add_node("safety_guardrail", wrap_node("safety_guardrail"))

        # Original safety (Layer 5) flows into response
        workflow.add_edge("safety", "response")
        # Final Guardrail check after response generation
        workflow.add_edge("response", "safety_guardrail")
        workflow.add_edge("safety_guardrail", END)

        return workflow.compile()

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return "ar" if lang == "ar" else "en"
        except:
            return "en"

    async def run(self, initial_input: str, user_id: str = "guest", image_path: str = None, request_second_opinion: bool = False, interaction_mode: str = None):
        persistence = self.get_agent("persistence")
        sanitized = sanitize_input(initial_input)
        is_valid, error_msg = validate_medical_input(sanitized)
        if not is_valid:
            return {"final_response": f"Input validation failed: {error_msg}.", "status": "error"}
        
        user_profile = {}
        if user_id != "guest":
            from database.models import UserAccount, PatientProfile
            # Need to use async DB in async run
            async with AsyncSessionLocal() as db:
                try:
                    stmt = select(UserAccount).filter(UserAccount.id == user_id)
                    res = await db.execute(stmt)
                    user_acc = res.scalars().first()
                    if user_acc:
                        user_profile = {
                            "role": user_acc.role if hasattr(user_acc.role, 'value') else user_acc.role,
                            "gender": user_acc.gender,
                            "age": user_acc.age,
                            "country": user_acc.country,
                            "interaction_mode": user_acc.interaction_mode,
                            "doctor_verified": user_acc.doctor_verified
                        }
                        p_stmt = select(PatientProfile).filter(PatientProfile.id == user_id)
                        p_res = await db.execute(p_stmt)
                        patient_p = p_res.scalars().first()
                        if patient_p and patient_p.medical_history_encrypted:
                            user_profile["medical_background"] = patient_p.medical_history_encrypted
                except Exception as e:
                    logger.error(f"Error fetching user profile in async run: {e}")
        
        final_mode = interaction_mode or user_profile.get("interaction_mode", "patient")
        session_id = await persistence.create_session(user_id=user_id, mode=final_mode)
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
                "conversation_state": {"active_case_id": None, "risk_level": "unknown", "pending_actions": []},
                "retry_reason": "",
                "correction_count": 0
            }
            
            # Since LangGraph 0.1+ supports async natively if nodes are synchronous (handled by LangGraph threadpool)
            final_state = await self.graph.ainvoke(state)
            
            await persistence.save_interaction(
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
