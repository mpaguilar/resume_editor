"""LLM client initialization for orchestration."""

import logging
from typing import Any

from langchain_openai import ChatOpenAI

from resume_editor.app.llm.models import LLMConfig

log = logging.getLogger(__name__)

DEFAULT_LLM_TEMPERATURE = 0.2


def initialize_llm_client(llm_config: LLMConfig) -> ChatOpenAI:
    """Initializes the ChatOpenAI client from configuration.

    Args:
        llm_config: Configuration for the LLM client.

    Returns:
        An initialized ChatOpenAI client instance.

    Notes:
        1. Determines the model name, using provided llm_model_name or default.
        2. Sets up LLM parameters for temperature, endpoint, and headers.
        3. Sets the API key if provided, or uses a dummy key for custom endpoints.

    """
    _msg = "initialize_llm_client starting"
    log.debug(_msg)

    model_name = llm_config.llm_model_name if llm_config.llm_model_name else "gpt-4o"
    llm_params: dict[str, Any] = {
        "model": model_name,
        "temperature": DEFAULT_LLM_TEMPERATURE,
    }
    if llm_config.llm_endpoint:
        llm_params["openai_api_base"] = llm_config.llm_endpoint
        if "openrouter.ai" in llm_config.llm_endpoint:
            llm_params["default_headers"] = {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            }
    if llm_config.api_key:
        llm_params["api_key"] = llm_config.api_key
    elif llm_config.llm_endpoint and "openrouter.ai" not in llm_config.llm_endpoint:
        llm_params["api_key"] = "not-needed"

    _msg = "initialize_llm_client returning"
    log.debug(_msg)
    return ChatOpenAI(**llm_params)
