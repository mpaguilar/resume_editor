"""Tests for orchestration_client module."""

from unittest.mock import patch

import pytest

from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration_client import (
    DEFAULT_LLM_TEMPERATURE,
    initialize_llm_client,
)


def test_initialize_llm_client_default_model():
    """Test LLM client initialization with default model."""
    config = LLMConfig(api_key="test-key")
    with patch("resume_editor.app.llm.orchestration_client.ChatOpenAI") as mock_chat:
        initialize_llm_client(config)
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["temperature"] == DEFAULT_LLM_TEMPERATURE
        assert call_kwargs["api_key"] == "test-key"


def test_initialize_llm_client_custom_endpoint():
    """Test LLM client with custom endpoint."""
    config = LLMConfig(
        api_key="test-key",
        llm_endpoint="https://custom.api.com",
        llm_model_name="custom-model",
    )
    with patch("resume_editor.app.llm.orchestration_client.ChatOpenAI") as mock_chat:
        initialize_llm_client(config)
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["openai_api_base"] == "https://custom.api.com"
        assert call_kwargs["model"] == "custom-model"


def test_initialize_llm_client_openrouter():
    """Test LLM client with OpenRouter endpoint."""
    config = LLMConfig(
        api_key="test-key",
        llm_endpoint="https://openrouter.ai/api/v1",
    )
    with patch("resume_editor.app.llm.orchestration_client.ChatOpenAI") as mock_chat:
        initialize_llm_client(config)
        call_kwargs = mock_chat.call_args.kwargs
        assert "default_headers" in call_kwargs
        assert call_kwargs["default_headers"]["X-Title"] == "Resume Editor"


def test_initialize_llm_client_no_key_custom_endpoint():
    """Test LLM client without API key for custom endpoint."""
    config = LLMConfig(llm_endpoint="https://custom.api.com")
    with patch("resume_editor.app.llm.orchestration_client.ChatOpenAI") as mock_chat:
        initialize_llm_client(config)
        call_kwargs = mock_chat.call_args.kwargs
        assert call_kwargs["api_key"] == "not-needed"
