"""
Second Opinion Agent - External specialist simulation.
Provides a critical review of the primary reasoning for complex cases.
"""
from .state import AgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings
import logging

logger = logging.getLogger(__name__)

class SecondOpinionAgent:
    def __init__(self, model=None):
        model = model or settings.OPENAI_MODEL
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.3, # Slightly more critical
            api_key=settings.OPENAI_API_KEY
        )

    def process(self, state: AgentState):
        """Review the existing reasoning and provide a second clinical perspective."""
        print("--- SECOND OPINION AGENT: CRITICAL REVIEW ---")
        
        # Only trigger if the user requested it or if confidence is low
        if not state.get("request_second_opinion") and state.get("confidence_score", 1.0) > 0.6:
            return state

        primary_diagnosis = state.get("preliminary_diagnosis", "")
        patient_summary = state.get("patient_info", {}).get("summary", "")
        
        prompt = f"""
        Current Patient Summary: {patient_summary}
        Primary Reasoning/Diagnosis: {primary_diagnosis}
        
        As a Senior Medical Specialist, provide a critical 'Second Opinion'. 
        - Are there any rare conditions missed?
        - Is the current plan too aggressive or too passive?
        - Suggest one additional diagnostic test.
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a skeptical and thorough Medical Specialist providing a second opinion."),
                HumanMessage(content=prompt)
            ])
            state["second_opinion"] = response.content
            # Append to final response if requested
            state["final_response"] += f"\n\n---\n**👨‍⚕️ Second Opinion Insight:**\n{response.content}"
        except Exception as e:
            logger.error(f"Second opinion failure: {e}")
            
        return state
