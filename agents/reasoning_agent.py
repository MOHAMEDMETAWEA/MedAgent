"""
Reasoning Agent (formerly Diagnosis Agent) - detailed analysis.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from config import settings, get_prompt_path
import logging

logger = logging.getLogger(__name__)

class ReasoningAgent:
    """
    Analyzes symptoms and evidence to generate a reasoning chain/differential.
    """
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model, 
            temperature=settings.LLM_TEMPERATURE_DIAGNOSIS,
            api_key=settings.OPENAI_API_KEY
        )

    def _load_prompt(self, filename: str) -> str:
        return get_prompt_path(filename).read_text(encoding='utf-8')

    def process(self, state: AgentState):
        print("--- REASONING AGENT: DIFFERENTIAL DIAGNOSIS ---")
        patient_summary = state.get('patient_info', {}).get('summary', '')
        knowledge = state.get('retrieved_docs', '')
        
        if not patient_summary:
            return {"preliminary_diagnosis": "No sufficient information.", "next_step": "validation"}

        try:
            # Reuse diagnosis prompt but as reasoning
            prompt_template = self._load_prompt('diagnosis_agent.txt')
            prompt = prompt_template.format(
                knowledge=knowledge, 
                patient_summary=patient_summary
            )
            
            response = self.llm.invoke([
                SystemMessage(content="You are a Medical Reasoning Agent. Use ONLY the provided guidelines. Be explicit about uncertainty."),
                HumanMessage(content=prompt)
            ])
            
            return {
                "preliminary_diagnosis": response.content,
                "next_step": "validation"
            }
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return {
                "preliminary_diagnosis": "Error in reasoning phase.",
                "next_step": "validation" # Pass to validation to catch/fix
            }
