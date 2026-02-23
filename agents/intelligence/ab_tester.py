"""
A/B Testing Framework.
Compares two clinical prompt versions against synthetic and real cases.
"""
import json
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts.registry import PROMPT_REGISTRY
from config import settings

logger = logging.getLogger(__name__)

class ABTester:
    """
    Experimental framework to compare prompt performance 
    with a bias towards clinical safety.
    """
    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY
        )

    def run_comparison(self, prompt_id: str, prompt_a_content: str, prompt_b_content: str, test_cases: List[Dict[str, Any]]):
        """
        Runs both prompt versions against test cases and identifies a winner.
        """
        logger.info(f"--- A/B TEST: COMPARING TWO VERSIONS OF {prompt_id} ---")
        
        comparison_results = []
        
        for case in test_cases:
            # Simulation: Invoke both versions
            res_a = self._sim_invoke(prompt_a_content, case)
            res_b = self._sim_invoke(prompt_b_content, case)
            
            comparison_results.append({
                "case": case["id"],
                "results_a": res_a,
                "results_b": res_b
            })

        # Final Evaluation via LLM
        eval_prompt_entry = PROMPT_REGISTRY.get("MED-AB-EVAL-001")
        if not eval_prompt_entry:
            return {"error": "A/B Evaluation prompt not found."}

        eval_prompt = eval_prompt_entry.content + f"\n\nDATA:\n{json.dumps(comparison_results, indent=2)}"

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a Clinical Trials Data Auditor."),
                HumanMessage(content=eval_prompt)
            ])
            
            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                return json.loads(content[start:end])
            return {"raw_outcome": content}

        except Exception as e:
            logger.error(f"A/B Test error: {e}")
            return {"error": str(e)}

    def _sim_invoke(self, content: str, case: Dict[str, Any]) -> str:
        """
        Simulates an LLM invocation with a specific prompt content.
        """
        # In production, this would actually call the model
        return f"Simulated response using prompt content: {content[:50]}..."
