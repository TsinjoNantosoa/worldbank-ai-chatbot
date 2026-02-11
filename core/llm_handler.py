"""
LLM Handler - Wrapper pour ChatOpenAI avec gestion d'erreurs

Configuration et invocation du modèle LLM
"""

import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def setup_llm(config: Dict[str, Any]) -> ChatOpenAI:
    """
    Configure et retourne une instance ChatOpenAI
    
    Args:
        config: Configuration dict (openai_api_key, model, etc.)
        
    Returns:
        Instance ChatOpenAI configurée
    """
    model_name = config.get("model", "gpt-4o-mini")
    temperature = config.get("temperature", 0.0)
    max_tokens = config.get("max_tokens", 1500)
    
    logger.info(f"Setting up LLM: {model_name} (temp={temperature}, max_tokens={max_tokens})")
    
    llm = ChatOpenAI(
        openai_api_key=config["openai_api_key"],
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        request_timeout=60
    )
    
    logger.info("✅ LLM initialized")
    
    return llm
