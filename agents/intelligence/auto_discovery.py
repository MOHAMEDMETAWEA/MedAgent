"""
Auto-Discovery Subsystem.
Analyzes logs and feedback to detect prompt blind spots and hallucinations.
"""
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts.registry import PROMPT_REGISTRY
from config import settings

logger = logging.getLogger(__name__)

class AutoDiscoveryAgent:
    """
    Subsystem designed to continuously analyze system performance 
    and recommend prompt evolutions without direct modification.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )

    def analyze(self, logs: str, feedback: str, escalations: str, hallucinations: str):
        """
        Analyzes multi-source data to detect system blind spots.
        """
        logger.info("--- AUTO-DISCOVERY: ANALYZING SYSTEM LOGS & FEEDBACK ---")
        
        prompt_entry = PROMPT_REGISTRY.get("MED-INT-DISCOVERY-001")
        if not prompt_entry:
            logger.error("MED-INT-DISCOVERY-001 not found in registry.")
            return {"error": "Discovery prompt not found in registry."}

        # Format the discovery prompt with incoming aggregate data
        analysis_prompt = prompt_entry.content.format(
            logs=logs,
            feedback=feedback,
            escalations=escalations,
            hallucinations=hallucinations
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Clinical AI Meta-Auditor for hospital-grade systems."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Extract JSON from response
            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                return json.loads(content[start:end])
            return {"raw_analysis": content}

        except Exception as e:
            logger.error(f"Auto-Discovery analysis error: {e}")
            return {"error": str(e)}

    def get_discovery_triggers(self):
        """
        Returns the thresholds that trigger auto-discovery.
        """
        return {
            "hallucination_threshold": 0.05,  # >5% triggers deep audit
            "escalation_threshold": 0.10,    # >10% triggers category scan
            "low_confidence_threshold": 0.20 # >20% triggers prompt refactoring proposal
        }
