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
        from langchain_openai import ChatOpenAI
        from config import settings
        model = state.get("model_used") or self.default_model
        return ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_DIAGNOSIS,
            api_key=settings.OPENAI_API_KEY
        )

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
            base_template = self._load_prompt("clinical_cognitive_layer.txt")
            context_data = f"PATIENT SUMMARY: {patient_summary}\nVISUAL: {visual}\nHISTORY: {history}"
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
            risk_level = state.get("risk_level", "low").lower()
            
            if risk_level not in ["high", "emergency"]:
                logger.info("--- REASONING AGENT: FAST PATH ---")
                direct_prompt = f"SYSTEM: You are a Cognitive Medical Reasoning Core. {routing_prompt}"
                response = llm.invoke([
                    SystemMessage(content="You are a direct Clinical Reasoning AI."),
                    HumanMessage(content=direct_prompt)
                ])
                diag = response.content
                conf = 0.8
            else:
                tot_prompt = f"TASK: Generate 3 distinct medical reasoning branches.\n{routing_prompt}"
                paths_response = llm.invoke([
                    SystemMessage(content="You are a Tree-of-Thought Medical Orchestrator."),
                    HumanMessage(content=tot_prompt)
                ])
                
                eval_prompt = f"Select the BEST branch from:\n{paths_response.content}\nReturn JSON: {{'diagnosis': '...', 'confidence_score': 0.0}}"
                final_selection = llm.invoke([
                    SystemMessage(content="You are a Medical Expert Board Auditor."),
                    HumanMessage(content=eval_prompt)
                ])
                
                content = final_selection.content
                if "{" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    data = json.loads(content[start:end])
                    diag = data.get("diagnosis", content)
                    conf = data.get("confidence_score", 0.7)
                else:
                    diag = content
                    conf = 0.65
            
            return {
                "preliminary_diagnosis": diag,
                "confidence_score": conf,
                "next_step": "validation",
                "status": "Reasoning Complete"
            }

        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return {"preliminary_diagnosis": "Critical error during reasoning phase.", "next_step": "validation"}
