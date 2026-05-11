"""
Risk-Weighted Router Controller.
Intelligently selects AI models based on clinical risk stratification and query complexity.
"""

import json
import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.prompts.registry import PROMPT_REGISTRY
from config import settings

logger = logging.getLogger(__name__)


class RiskRouter:
    """
    Controller responsible for routing queries to appropriate models
    to balance cost, speed, and clinical accuracy.
    """

    def __init__(self, model=None):
        self.llm = ChatOpenAI(
            model=model or settings.OPENAI_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
        )

    def route(self, user_query: str, clinical_context: Dict[str, Any]):
        """
        Determines the optimal model and safety protocol for a given interaction.
        """
        logger.info("--- RISK ROUTER: ANALYZING CLINICAL COMPLEXITY ---")

        router_prompt_entry = PROMPT_REGISTRY.get("MED-RT-ROUTER-001")
        if not router_prompt_entry:
            return {"error": "Router prompt not found."}

        prompt = (
            router_prompt_entry.content
            + f"\n\nQUERY: {user_query}\nCONTEXT: {json.dumps(clinical_context)}"
        )

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(
                        content="You are a Medical Systems Architect and Triage Orchestrator."
                    ),
                    HumanMessage(content=prompt),
                ]
            )

            content = response.content
            if "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                result = json.loads(content[start:end])

                # Apply model selection defaults
                result["selected_model"] = settings.OPENAI_MODEL
                result["secondary_model"] = settings.OPENAI_MODEL
                result["cross_check_required"] = result.get(
                    "cross_check_required", False
                )

                return result
            return {"raw_routing": content}

        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {"error": str(e)}

    def get_fallback_chain(self):
        """
        Returns the model fallback hierarchy for system resilience.
        """
        return {
            "primary": "gpt-4o",
            "secondary": "gpt-4o-mini",
            "tertiary": "gpt-3.5-turbo (legacy fallback)",
        }
