"""
LLM SETUP - Centralized Model Configuration
=============================================

Single source of truth for LLM model initialization and configuration.
Consolidates model setup logic from feature_by_request_agent_v3.py.
"""

import os
from typing import Optional, Tuple
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def setup_model(
    model_override: Optional[str] = None,
    temperature_override: Optional[float] = None
) -> Tuple[str, float, ChatOpenAI]:
    """
    Setup LLM model with credentials from environment.
    
    Single function for all LLM initialization across the pipeline.
    
    Args:
        model_override: Override model name from environment
        temperature_override: Override temperature calculation
    
    Returns:
        Tuple of (model_name, temperature, model_instance)
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Get model from args or environment
    model_name = model_override or os.getenv("LITELLM_MODEL", "gpt-4o-mini")

    # Get temperature: auto-set based on model, or user override
    is_reasoning = any(
        kw in model_name.lower() 
        for kw in ["gpt-5", "5-mini", "oss", "120b", "reasoning"]
    )
    temperature = (
        temperature_override 
        if temperature_override is not None 
        else (1.0 if is_reasoning else 0.7)
    )

    # Setup API credentials
    api_key = os.getenv("LITELLM_VIRTUAL_KEY")
    api_base = os.getenv("LITELLM_API")

    if not api_key or not api_base:
        raise ValueError(
            "Missing required environment variables:\n"
            "  LITELLM_VIRTUAL_KEY: LLM API key\n"
            "  LITELLM_API: LLM API base URL"
        )

    # Create model instance
    model = ChatOpenAI(
        api_key=SecretStr(api_key),
        model=model_name,
        base_url=api_base,
        temperature=temperature,
        default_headers={
            "X-Api-Key": api_key,
            "Authorization": f"Bearer {api_key}"
        }
    )
    
    return model_name, temperature, model


def get_model_config(model_instance: ChatOpenAI) -> dict:
    """
    Get current model configuration.
    
    Args:
        model_instance: ChatOpenAI model instance
        
    Returns:
        Dictionary with model configuration
    """
    return {
        "model": model_instance.model_name if hasattr(model_instance, "model_name") else "unknown",
        "temperature": model_instance.temperature if hasattr(model_instance, "temperature") else 0.7,
    }
