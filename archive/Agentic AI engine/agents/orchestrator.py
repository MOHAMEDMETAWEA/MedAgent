"""
Multi-Agent Orchestrator - Global Generic Architecture.
Optimized for performance with lazy agent loading.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage
from langdetect import detect
from langgraph.graph import END, StateGraph

from config import settings
from utils.safety import sanitize_input, validate_medical_input

from .state import AgentState

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
        """Standard mapping of nodes to agent instances (Cached)."""
        if name in self._agents:
            return self._agents[name]

        from .clinical_review_agent import ClinicalReviewAgent
        from .diagnosis_agent import DiagnosisAgent
        from .hallucination_detector import HallucinationDetector
        from .knowledge_agent import KnowledgeAgent
        from .mental_health_agent import MentalHealthAgent
        from .patient_agent import PatientAgent
        from .pediatric_agent import PediatricAgent
        from .persistence_agent import PersistenceAgent
        from .pregnancy_agent import PregnancyAgent
        from .reasoning_agent import ReasoningAgent
        from .report_agent import ReportAgent
        from .response_agent import ResponseAgent
        from .safety_agent import SafetyAgent
        from .safety_guardrail_agent import SafetyGuardrailAgent
        from .soap_agent import SoapAgent
        from .supervisor_agent import SupervisorAgent
        from .triage_agent import TriageAgent
        from .uncertainty_calibrator import UncertaintyCalibrator
        from .validation_agent import ValidationAgent
        from .vision_agent import VisionAnalysisAgent

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
            "vision": VisionAnalysisAgent,
            "diagnosis": DiagnosisAgent,
            "report": ReportAgent,
            "clinical_review": ClinicalReviewAgent,
            "safety_guardrail": SafetyGuardrailAgent,
            "pediatric": PediatricAgent,
            "maternity": PregnancyAgent,
            "mental_health": MentalHealthAgent,
            "hallucination": HallucinationDetector,
            "calibrator": UncertaintyCalibrator,
            "soap": SoapAgent,
        }

        if name in agents_map:
            self._agents[name] = agents_map[name]()
            return self._agents[name]
        return None

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        import inspect

        def wrap_node(node_name):
            # Pre-fetch agent to determine async status once
            agent = self.get_agent(node_name)
            if not agent:
                raise RuntimeError(
                    f"Critical Error: Agent {node_name} failed to initialize."
                )

            # Determine method and async status
            method_name = "run" if hasattr(agent, "run") else "process"
            method = getattr(agent, method_name)
            is_async = inspect.iscoroutinefunction(method)

            async def wrapper(state: AgentState):
                try:
                    if is_async:
                        return await method(state)
                    return method(state)
                except Exception as e:
                    logger.error(f"--- NODE FAILURE: {node_name} --- Error: {e}")
                    # Cycle 5: Autonomous Fallback System
                    from learning.model_registry import model_registry

                    fallback = model_registry.get_fallback_model()
                    logger.warning(
                        f"Self-Healing: Triggering Fallback Model {fallback.get('version')} for {node_name}"
                    )

                    # Store fallback attempt in state for auditing
                    state["model_fallback_triggered"] = True
                    state["original_error"] = str(e)

                    # Re-run with the same method (the agent logic should use the registry or we re-instantiate)
                    # For simplicity in this architecture, we retry the call once.
                    # A more robust fix would involve re-injecting the fallback model into the agent instance.
                    try:
                        if hasattr(agent, "llm"):
                            # Dynamic model swap if the agent exposes its LLM
                            from models.model_router import get_model

                            agent.llm = get_model(model_name=fallback.get("version"))

                        if is_async:
                            return await method(state)
                        return method(state)
                    except Exception as fatal_e:
                        logger.critical(
                            f"FATAL: Fallback also failed for {node_name}. Error: {fatal_e}"
                        )
                        state["status"] = "error"
                        state["final_response"] = (
                            "The medical intelligence system is currently undergoing automated recovery. Please retry in 30 seconds."
                        )
                        return state

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
        workflow.add_node("safety_guardrail", wrap_node("safety_guardrail"))

        # Cycle 5: Specialty Adapters + Safety + Documentation
        workflow.add_node("pediatric", wrap_node("pediatric"))
        workflow.add_node("maternity", wrap_node("maternity"))
        workflow.add_node("mental_health", wrap_node("mental_health"))
        workflow.add_node("hallucination", wrap_node("hallucination"))
        workflow.add_node("calibrator", wrap_node("calibrator"))
        workflow.add_node("soap", wrap_node("soap"))

        # ===== EDGE STRUCTURE (No Conflicts) =====

        # 1. Parallel Entry: Vision + Patient
        def route_start(state: AgentState):
            if state.get("image_path"):
                return ["vision", "patient"]
            return ["patient"]

        workflow.set_conditional_entry_point(
            route_start, {"vision": "vision", "patient": "patient"}
        )

        # 2. Both converge into Triage
        workflow.add_edge("vision", "triage")
        workflow.add_edge("patient", "triage")

        # 3. Triage → Knowledge or Human Review
        def route_triage(state: AgentState):
            if state.get("risk_level") in ["High", "Emergency"] and not state.get(
                "doctor_verified"
            ):
                return "review"
            return "knowledge"

        workflow.add_conditional_edges(
            "triage", route_triage, {"review": "review", "knowledge": "knowledge"}
        )

        workflow.add_edge("review", END)  # Pause for human review

        # 4. Core reasoning pipeline
        workflow.add_edge("knowledge", "reasoning")
        workflow.add_edge("reasoning", "validation")

        # 5. Self-Correction Loop
        def route_validation(state: AgentState):
            if (
                state.get("validation_status") == "invalid"
                and state.get("correction_count", 0) < 2
            ):
                logger.warning(
                    f"--- RE-ROUTING TO REASONING (Correction #{state.get('correction_count', 0) + 1}) ---"
                )
                return "retry"
            return "continue"

        workflow.add_conditional_edges(
            "validation",
            route_validation,
            {"retry": "reasoning", "continue": "hallucination"},
        )

        # 6. Safety Pipeline: Hallucination → Calibrator → Safety
        workflow.add_edge("hallucination", "calibrator")
        workflow.add_edge("calibrator", "safety")

        # 7. Specialty Routing (after Safety)
        def route_specialty(state: AgentState):
            if state.get("user_age", 0) and 0 < state.get("user_age", 0) < 18:
                return "pediatric"
            if state.get("patient_info", {}).get("is_pregnant"):
                return "maternity"
            if state.get("triage_category") == "Mental Health" or state.get(
                "mental_health_screening"
            ):
                return "mental_health"
            return "response"

        workflow.add_conditional_edges(
            "safety",
            route_specialty,
            {
                "pediatric": "pediatric",
                "maternity": "maternity",
                "mental_health": "mental_health",
                "response": "response",
            },
        )

        # 8. All paths converge into Safety Guardrail (final check)
        workflow.add_edge("pediatric", "safety_guardrail")
        workflow.add_edge("maternity", "safety_guardrail")
        workflow.add_edge("mental_health", "safety_guardrail")
        workflow.add_edge("response", "safety_guardrail")

        # 9. Safety Guardrail → SOAP → END
        workflow.add_edge("safety_guardrail", "soap")
        workflow.add_edge("soap", END)

        return workflow.compile()

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return "ar" if lang == "ar" else "en"
        except Exception:
            return "en"

    async def run(
        self,
        initial_input: str,
        user_id: str = "guest",
        image_path: str = None,
        request_second_opinion: bool = False,
        interaction_mode: str = None,
    ):
        persistence = self.get_agent("persistence")
        sanitized = sanitize_input(initial_input)
        is_valid, error_msg = validate_medical_input(sanitized)
        if not is_valid:
            return {
                "final_response": f"Input validation failed: {error_msg}.",
                "status": "error",
            }

        user_profile = {}
        ehr_data = {}

        # Phase 2: EHR Integration (Hospital-Grade)
        from integrations.ehr_integration import ehr_manager

        if user_id != "guest":
            ehr_data = await ehr_manager.sync_patient_record(user_id)

            from sqlalchemy import select

            from database.models import (AsyncSessionLocal, PatientProfile,
                                         UserAccount)

            async with AsyncSessionLocal() as db:
                try:
                    stmt = select(UserAccount).filter(UserAccount.id == user_id)
                    res = await db.execute(stmt)
                    user_acc = res.scalars().first()
                    if user_acc:
                        user_profile = {
                            "role": (
                                user_acc.role
                                if hasattr(user_acc.role, "value")
                                else user_acc.role
                            ),
                            "gender": user_acc.gender,
                            "age": user_acc.age,
                            "country": user_acc.country,
                            "interaction_mode": user_acc.interaction_mode,
                            "doctor_verified": user_acc.doctor_verified,
                        }
                        p_stmt = select(PatientProfile).filter(
                            PatientProfile.id == user_id
                        )
                        p_res = await db.execute(p_stmt)
                        patient_p = p_res.scalars().first()
                        if patient_p and patient_p.medical_history_encrypted:
                            user_profile["medical_background"] = (
                                patient_p.medical_history_encrypted
                            )
                except Exception as e:
                    logger.error(f"Error fetching user profile in async run: {e}")

        final_mode = interaction_mode or user_profile.get("interaction_mode", "patient")
        session_id = await persistence.create_session(user_id=user_id, mode=final_mode)
        lang = self.detect_language(sanitized)

        # Load conversation history for multi-turn session memory
        history = await persistence.get_session_history(session_id)
        past_messages = []

        for h in history:
            past_messages.append(HumanMessage(content=h["user"]))
            past_messages.append(AIMessage(content=h["ai"]))

        # Phase 11: Scalability - Prediction Caching
        from intelligence.inference_cache import inference_cache

        cached_result = inference_cache.get_prediction(sanitized, final_mode)
        if cached_result:
            return cached_result

        from learning.model_registry import model_registry

        current_model = model_registry.get_latest_model()

        try:
            state = {
                "messages": past_messages + [HumanMessage(content=sanitized)],
                "user_id": user_id,
                "session_id": session_id,
                "patient_info": {"ehr": ehr_data, "vitals": ehr_data.get("vitals", {})},
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
                "conversation_state": {
                    "active_case_id": None,
                    "risk_level": "unknown",
                    "pending_actions": [],
                },
                "retry_reason": "",
                "correction_count": 0,
                "prompt_version": current_model.get("version", "1.0.0"),
                "model_used": current_model.get("version", "base"),
            }

            # Phase 3: Real-Time Monitoring
            from monitoring.realtime_engine import monitoring_engine

            if state["patient_info"]["vitals"]:
                vitals_status = await monitoring_engine.update_vitals(
                    user_id, state["patient_info"]["vitals"]
                )
                if vitals_status.get("status") == "CRITICAL":
                    state["critical_alert"] = True
                    state["safety_status"] = "EMERGENCY_ESCALATION"

            # Phase 4: Multi-Doctor Collaboration
            from collaboration.case_workspace import case_workspace

            if request_second_opinion:
                case_id = f"CASE-{session_id[-8:]}"
                await case_workspace.create_case(case_id, sanitized, user_id)
                state["conversation_state"]["active_case_id"] = case_id
                logger.info(f"Collaboration: Initiated workspace for Case {case_id}")

            # Run AI Orchestration
            final_state = await self.graph.ainvoke(state)

            # Phase 9: Smart Notifications (Emergency Alerts)
            from notifications.engine import notification_engine

            if final_state.get("risk_level") in ["EMERGENCY", "CRITICAL"] or final_state.get(
                "critical_alert"
            ):
                await notification_engine.send_alert(
                    user_id=user_id,
                    title="🚨 CLINICAL EMERGENCY ALERT",
                    message=f"Critical risk detected: {final_state.get('preliminary_diagnosis')}. Seek immediate help.",
                    priority="EMERGENCY",
                )

            # Performance: Cache the result
            inference_cache.set_prediction(sanitized, final_mode, final_state)

            await persistence.save_interaction(
                session_id=session_id, user_input=sanitized, result=final_state
            )
            return final_state
        except Exception as e:
            logger.error(f"Orchestrator run error: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {
                "final_response": "The system encountered a critical error. Please try again.",
                "status": "error",
            }

    async def stream_run(
        self,
        initial_input: str,
        user_id: str = "guest",
        image_path: str = None,
        request_second_opinion: bool = False,
        interaction_mode: str = None,
    ):
        """
        Asynchronous generator that yields state updates for real-time progress tracking.
        """
        persistence = self.get_agent("persistence")
        sanitized = sanitize_input(initial_input)

        # Identity retrieval
        user_profile = {}
        ehr_data = {}
        from integrations.ehr_integration import ehr_manager

        if user_id != "guest":
            ehr_data = await ehr_manager.sync_patient_record(user_id)
            from sqlalchemy import select

            from database.models import AsyncSessionLocal, UserAccount

            async with AsyncSessionLocal() as db:
                try:
                    stmt = select(UserAccount).filter(UserAccount.id == user_id)
                    res = await db.execute(stmt)
                    user_acc = res.scalars().first()
                    if user_acc:
                        user_profile = {
                            "role": getattr(user_acc.role, "value", user_acc.role),
                            "doctor_verified": user_acc.doctor_verified,
                            "interaction_mode": user_acc.interaction_mode,
                        }
                except Exception:
                    pass

        final_mode = interaction_mode or user_profile.get("interaction_mode", "patient")
        session_id = await persistence.create_session(user_id=user_id, mode=final_mode)

        # History
        history = await persistence.get_session_history(session_id)
        past_messages = []

        for h in history:
            past_messages.append(HumanMessage(content=h["user"]))
            past_messages.append(AIMessage(content=h["ai"]))

        from learning.model_registry import model_registry

        current_model = model_registry.get_latest_model()

        state = {
            "messages": past_messages + [HumanMessage(content=sanitized)],
            "user_id": user_id,
            "session_id": session_id,
            "patient_info": {"ehr": ehr_data, "vitals": ehr_data.get("vitals", {})},
            "final_response": "",
            "status": "Initializing...",
            "image_path": image_path,
            "request_second_opinion": request_second_opinion,
            "interaction_mode": final_mode,
            "prompt_version": current_model.get("version", "1.0.0"),
            "model_used": current_model.get("version", "base"),
        }

        # Yield status updates
        try:
            async for event in self.graph.astream(state):
                for node_name, output in event.items():
                    logger.info(f"Node Complete: {node_name}")
                    yield {
                        "node": node_name,
                        "status": output.get("status", f"Processing {node_name}..."),
                        "preliminary_diagnosis": output.get("preliminary_diagnosis"),
                        "final_response": output.get("final_response"),
                        "session_id": session_id,
                    }
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "node": "error",
                "status": f"System Error: {str(e)}",
                "session_id": session_id,
            }
