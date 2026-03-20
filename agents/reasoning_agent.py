"""
Reasoning Agent with Tree-of-Thought (ToT) Architecture.
Optimized for performance with lazy imports.
"""
import logging
import json

logger = logging.getLogger(__name__)

class ReasoningAgent:
    def __init__(self, model=None):
        from config import settings
        self.default_model = model or settings.OPENAI_MODEL

    def _get_llm(self, state: dict):
        from models.model_router import get_model
        from config import settings
        model = state.get("model_used") or self.default_model
        return get_model(model_name=model, temperature=settings.LLM_TEMPERATURE_DIAGNOSIS)

    def _load_prompt(self, filename: str) -> str:
        from config import get_prompt_path
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except: return "Diagnose the following symptoms based on knowledge: {knowledge}\nSymptoms: {patient_summary}"

    def process(self, state: dict):
        from langchain_core.messages import SystemMessage, HumanMessage
        from config import settings
        
        logger.info("--- REASONING AGENT: TREE-OF-THOUGHT ANALYSIS ---")
        patient_summary = state.get('patient_info', {}).get('summary', '')
        knowledge = state.get('retrieved_docs', '')
        visual = state.get('visual_findings', {})
        history = state.get('long_term_memory', '')
        
        if not patient_summary:
            return {"preliminary_diagnosis": "Insufficient data for reasoning.", "next_step": "validation"}

        mode = state.get("interaction_mode", "patient")
        verified = state.get("doctor_verified", False)
        role = state.get("user_role", "patient")
        age = state.get("user_age", "Unknown")
        gender = state.get("user_gender", "Unknown")
        country = state.get("user_country", "Unknown")
        
        edu = state.get("education_level", "unknown")
        lit = state.get("medical_literacy_level", "moderate")
        emo = state.get("emotional_state", "calm")
        
        try:
            from intelligence.cdss_engine import cdss_engine
            from explainability.clinical_explainer import clinical_explainer
            
            # Phase 5: Integrate CDSS Risk Analysis
            cdss_data = await cdss_engine.generate_cdss_payload(state)
            state["risk_level"] = cdss_data["cdss_risk"]
            state["cdss_score"] = cdss_data["cdss_score"]
            state["guideline_ref"] = cdss_data["guideline_ref"]

            base_template = self._load_prompt("clinical_cognitive_layer.txt")
            retry_context = f"\n\n[SELF-CORRECTION FEEDBACK]: Your previous response had issues: {state.get('retry_reason')}. PLEASE CORRECT THESE." if state.get("retry_reason") else ""
            context_data = f"PATIENT SUMMARY: {patient_summary}\nVISUAL: {visual}\nHISTORY: {history}\nCDSS_RISK: {state['risk_level']}\nGUIDELINES: {state['guideline_ref']}{retry_context}"
            
            routing_prompt = base_template.format(
                mode=mode.upper(),
                role=role.upper(),
                verified=str(verified),
                age=age,
                gender=gender,
                country=country,
                education=edu.upper(),
                literacy=lit.upper(),
                emotion=emo.upper(),
                patient_data=context_data, 
                knowledge_base=knowledge
            )

            llm = self._get_llm(state)
            risk_level = state["risk_level"].lower()
            
            if risk_level not in ["high", "emergency"]:
                logger.info("--- REASONING AGENT: FAST PATH ---")
                explainable_prompt = f"{routing_prompt}\n\nIMPORTANT: Return a JSON object with: diagnosis, confidence, reasoning_steps (list), supporting_symptoms (list), evidence_sources (list), alternative_diagnoses (list)."
                response = await llm.ainvoke([
                    SystemMessage(content="You are a Clinical Explainability Core. Always provide structured reasoning."),
                    HumanMessage(content=explainable_prompt)
                ])
                content = response.content
            else:
                logger.info("--- REASONING AGENT: TREE-OF-THOUGHT (ToT) PATH ---")
                tot_prompt = f"TASK: Generate 3 distinct medical reasoning branches.\n{routing_prompt}"
                paths_response = await llm.ainvoke([
                    SystemMessage(content="You are a Tree-of-Thought Medical Orchestrator."),
                    HumanMessage(content=tot_prompt)
                ])
                
                eval_prompt = f"Select the BEST branch from:\n{paths_response.content}\nReturn a JSON object with: diagnosis, confidence, reasoning_steps (list), supporting_symptoms (list), evidence_sources (list), alternative_diagnoses (list)."
                final_selection = await llm.ainvoke([
                    SystemMessage(content="You are a Medical Expert Board Auditor."),
                    HumanMessage(content=eval_prompt)
                ])
                content = final_selection.content
            
            # Parse JSON and Wrap with ClinicalExplainer (Phase 8)
            diag = "Uncertain"
            conf = 0.5
            if "{" in content:
                try:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    raw_data = json.loads(content[start:end])
                    
                    diag = raw_data.get("diagnosis", "Uncertain")
                    conf = raw_data.get("confidence", 0.5)
                    state["reasoning_trace"] = raw_data.get("reasoning_steps", [])
                    state["retrieved_docs"] = "\n".join(raw_data.get("evidence_sources", []))
                    state["confidence_score"] = conf
                except Exception as e:
                    logger.warning(f"Failed to parse inner reasoning JSON: {e}")
                    diag = content
            else:
                diag = content

            # Generate Final Explanation (Role-Adapted)
            explanation = await clinical_explainer.generate_explanation(state, target_role=role)
            state["clinical_explanation"] = explanation

            # AUDIT LOGGING (Hospital-Grade)
            from utils.audit_logger import AuditLogger
            AuditLogger.log_agent_interaction(
                user_id=state.get("user_id", "unknown"),
                agent_name="ReasoningAgent",
                input_data=patient_summary,
                output_data=diag,
                model_used=self.default_model,
                confidence=conf,
                risk_level=risk_level
            )

            return {
                "preliminary_diagnosis": diag,
                "confidence_score": conf,
                "clinical_explanation": explanation,
                "risk_level": state["risk_level"],
                "next_step": "validation",
                "status": "Reasoning Complete",
                "correction_count": state.get("correction_count", 0) + (1 if state.get("retry_reason") else 0)
            }

        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return {"preliminary_diagnosis": f"Reasoning failure: {str(e)}", "next_step": "validation"}
