from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from agents.prompts.registry import PROMPT_REGISTRY
from config import settings
import logging
import json

logger = logging.getLogger(__name__)

class ConfidenceScorerAgent:
    """
    Post-reasoning confidence scorer.
    Uses MED-GOV-CONF-001 to assign a confidence score 0..1.
    """
    def __init__(self, model=None):
        self.default_model = model or settings.OPENAI_MODEL
    
    def score(self, diagnosis: str, state: dict) -> float:
        entry = PROMPT_REGISTRY.get("MED-GOV-CONF-001")
        if not entry or not diagnosis:
            return None
        model = state.get("model_used") or self.default_model
        llm = ChatOpenAI(model=model, temperature=0.0, api_key=settings.OPENAI_API_KEY)
        prompt = entry.content.format(diagnosis=diagnosis)
        try:
            resp = llm.invoke([
                SystemMessage(content="You are a Calibration Agent. Output only a number 0..1 or a short JSON with confidence_score."),
                HumanMessage(content=prompt)
            ])
            text = resp.content.strip()
            if "{" in text:
                try:
                    start = text.find("{"); end = text.rfind("}") + 1
                    data = json.loads(text[start:end])
                    return float(data.get("confidence_score"))
                except Exception:
                    pass
            # try to parse a bare float
            try:
                return min(1.0, max(0.0, float(text)))
            except Exception:
                return None
        except Exception as e:
            logger.error(f"Confidence scoring error: {e}")
            return None
