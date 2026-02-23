"""
Prompt Registry Management Engine (Governance).
Enforces versioning, risk classification, and safety gating for clinical prompts.
"""
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts.registry import PROMPT_REGISTRY, PromptEntry
from config import settings

logger = logging.getLogger(__name__)

class PromptGovernanceEngine:
    """
    Governance layer that ensures no prompt update occurs without 
    safety delta analysis and clinical impact scoring.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )

    def _calculate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def evaluate_update(self, prompt_id: str, new_content: str):
        """
        Evaluates a proposed change to a prompt.
        """
        logger.info(f"--- GOVERNANCE AUDIT: EVALUATING UPDATE FOR {prompt_id} ---")
        
        current_prompt = PROMPT_REGISTRY.get(prompt_id)
        if not current_prompt:
            return {"error": f"Prompt {prompt_id} not found."}

        old_hash = self._calculate_hash(current_prompt.content)
        new_hash = self._calculate_hash(new_content)

        if old_hash == new_hash:
            return {"status": "unchanged", "justification": "Content is identical."}

        governance_prompt_entry = PROMPT_REGISTRY.get("MED-GOV-REGISTRY-001")
        
        delta_report = f"OLD PROMPT:\n{current_prompt.content}\n\nNEW PROMPT:\n{new_content}"
        
        eval_prompt = governance_prompt_entry.content.format(
            old_hash=old_hash[:8],
            new_hash=new_hash[:8],
            delta_report=delta_report
        )

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Clinical Regulatory Compliance Inspector."),
                HumanMessage(content=eval_prompt)
            ])
            
            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                result = json.loads(content[start:end])
                result["old_hash"] = old_hash
                result["new_hash"] = new_hash
                return result
            return {"raw_analysis": content}

        except Exception as e:
            logger.error(f"Governance evaluation error: {e}")
            return {"error": str(e)}

    def get_risk_impact_matrix(self):
        """
        Defines deployment gates based on risk levels.
        """
        return {
            "emergency": "Manual SME Review + Medical Director Approval Required",
            "high": "Manual SME Review + Regression Test Required",
            "medium": "Automated Safety Check + Verifier Approval Required",
            "low": "Automated Safety Check Only"
        }
