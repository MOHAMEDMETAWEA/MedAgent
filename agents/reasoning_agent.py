"""
Reasoning Agent with Tree-of-Thought (ToT) Architecture.
Evaluates multiple diagnostic paths and selects the safest, most consistent one.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
import logging
import json

logger = logging.getLogger(__name__)

class ReasoningAgent:
    """
    Advanced Reasoning Agent:
    - Generates 3 unique Tree-of-Thought branches.
    - Evaluates branches for safety, consistency, and evidence.
    - Selects final outcome.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_DIAGNOSIS,
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename: str) -> str:
        try:
            return get_prompt_path(filename).read_text(encoding='utf-8')
        except: return "Diagnose the following symptoms based on knowledge: {knowledge}\nSymptoms: {patient_summary}"

    def process(self, state: AgentState):
        print("--- REASONING AGENT: TREE-OF-THOUGHT ANALYSIS ---")
        patient_summary = state.get('patient_info', {}).get('summary', '')
        knowledge = state.get('retrieved_docs', '')
        visual = state.get('visual_findings', {})
        history = state.get('long_term_memory', '')
        
        if not patient_summary:
            return {"preliminary_diagnosis": "Insufficient data for reasoning.", "next_step": "validation"}

        # Metadata for Adaptive Reasoning
        mode = state.get("interaction_mode", "patient")
        verified = state.get("doctor_verified", False)
        role = state.get("user_role", "patient")
        age = state.get("user_age")
        gender = state.get("user_gender")
        country = state.get("user_country")
        
        try:
            # 1. Load Routed Prompt Template
            template_name = "doctor_mode.txt" if mode == "doctor" else "patient_mode.txt"
            base_template = self._load_prompt(template_name)
            
            # Format the component prompt
            context_data = f"PATIENT SUMMARY: {patient_summary}\nVISUAL: {visual}\nHISTORY: {history}"
            routing_prompt = base_template.format(patient_data=context_data, knowledge_base=knowledge)

            # 2. Generate Multiple Thought Paths (ToT Stage)
            tot_prompt = f"""
            SYSTEM: You are a Cognitive Medical Reasoning Core. 
            USER INTERACTION MODE: {mode.upper()}
            USER ROLE: {role.upper()} (Verified: {verified})
            PATIENT DEMOGRAPHICS: Age {age}, Gender {gender}, Location {country}
            
            INSTRUCTION FROM ROUTING SYSTEM:
            {routing_prompt}

            TASK: Generate 3 distinct medical reasoning branches.
            - BRANCH 1: Conservative/Direct evidence only.
            - BRANCH 2: Contextual/History-linked (look for trends in past sessions).
            - BRANCH 3: Differential/Rare cases (edge cases or high-risk possibilities).

            Format each branch as:
            [BRANCH 1]: ...
            [BRANCH 2]: ...
            [BRANCH 3]: ...
            """
            
            paths_response = self.llm.invoke([
                SystemMessage(content="You are a Tree-of-Thought Medical Orchestrator."),
                HumanMessage(content=tot_prompt)
            ])
            
            eval_prompt = f"""
            Review the following 3 Reasoning Branches:
            {paths_response.content}

            Evaluate each for:
            1. Medical Consistency (Alignment with knowledge)
            2. Safety (Addressing high-risk indicators)
            3. Evidence Alignment (Clarity and direct mapping)

            Select the BEST branch. 
            Format your response as a JSON:
            {{
                "diagnosis": "The full reasoning of the best branch",
                "confidence_score": 0.0 to 1.0
            }}
            Do not mention that you are a tree of thought. Output final clinical reasoning.
            """
            
            final_selection = self.llm.invoke([
                SystemMessage(content="You are a Medical Expert Board Auditor."),
                HumanMessage(content=eval_prompt)
            ])
            
            try:
                # Attempt to parse JSON
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
            except:
                diag = final_selection.content
                conf = 0.6
            
            return {
                "preliminary_diagnosis": diag,
                "confidence_score": conf,
                "next_step": "validation",
                "status": "Tree-of-Thought Analysis Complete"
            }

        except Exception as e:
            logger.error(f"ToT Reasoning error: {e}")
            return {
                "preliminary_diagnosis": "Critical error during cognitive reasoning phase.",
                "next_step": "validation"
            }
