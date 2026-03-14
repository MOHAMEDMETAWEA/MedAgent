"""
Model Abstraction Layer - Routes LLM requests to Cloud (OpenAI) or Local providers.
"""
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from config import settings

logger = logging.getLogger(__name__)

def get_model(model_name: Optional[str] = None, temperature: float = 0.0, **kwargs):
    """
    Returns an LLM instance based on settings.MODEL_MODE.
    """
    mode = settings.MODEL_MODE.lower()
    
    if mode == "local":
        model_name = model_name or settings.LOCAL_MODEL_NAME
        logger.info(f"--- MODEL ROUTER: Routing to LOCAL provider ({model_name}) ---")
        
        # Check if vLLM or Ollama
        if "ollama" in kwargs.get("provider", "").lower() or settings.OLLAMA_URL:
            return ChatOllama(
                model=model_name,
                base_url=settings.OLLAMA_URL,
                temperature=temperature,
                **kwargs
            )
        else:
            # Fallback to OpenAI-compatible vLLM endpoint
            return ChatOpenAI(
                model=model_name,
                openai_api_base=settings.VLLM_URL,
                openai_api_key="EMPTY", # vLLM doesn't usually need a key
                temperature=temperature,
                **kwargs
            )
            
    # Default to Cloud (OpenAI)
    model_name = model_name or settings.OPENAI_MODEL
    logger.info(f"--- MODEL ROUTER: Routing to CLOUD provider ({model_name}) ---")
    return ChatOpenAI(
        model=model_name,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
        **kwargs
    )
