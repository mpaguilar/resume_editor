import logging
from unittest.mock import MagicMock, patch

from resume_editor.app.llm.models import LLMConfig
from resume_editor.app.llm.orchestration import _initialize_llm_client

log = logging.getLogger(__name__)


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
def test_initialize_llm_client_default(mock_chat_openai: MagicMock):
    """Test _initialize_llm_client with default config."""
    llm_config = LLMConfig()
    _initialize_llm_client(llm_config)
    mock_chat_openai.assert_called_once_with(
        model="gpt-4o",
        temperature=0.2,
    )


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
def test_initialize_llm_client_full_config(mock_chat_openai: MagicMock):
    """Test _initialize_llm_client with a full LLMConfig."""
    llm_config = LLMConfig(
        llm_endpoint="http://custom.endpoint/v1",
        api_key="custom_key",
        llm_model_name="custom-model",
    )
    _initialize_llm_client(llm_config)
    mock_chat_openai.assert_called_once_with(
        model="custom-model",
        temperature=0.2,
        openai_api_base="http://custom.endpoint/v1",
        api_key="custom_key",
    )


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
def test_initialize_llm_client_openrouter(mock_chat_openai: MagicMock):
    """Test _initialize_llm_client with OpenRouter endpoint."""
    llm_config = LLMConfig(
        llm_endpoint="https://openrouter.ai/api/v1",
        api_key="or_key",
    )
    _initialize_llm_client(llm_config)
    mock_chat_openai.assert_called_once_with(
        model="gpt-4o",
        temperature=0.2,
        openai_api_base="https://openrouter.ai/api/v1",
        api_key="or_key",
        default_headers={
            "HTTP-Referer": "http://localhost:8000/",
            "X-Title": "Resume Editor",
        },
    )


@patch("resume_editor.app.llm.orchestration.ChatOpenAI", autospec=True)
def test_initialize_llm_client_custom_endpoint_no_key(mock_chat_openai: MagicMock):
    """Test _initialize_llm_client with custom endpoint but no API key."""
    llm_config = LLMConfig(
        llm_endpoint="http://custom.endpoint/v1",
        api_key=None,
    )
    _initialize_llm_client(llm_config)
    mock_chat_openai.assert_called_once_with(
        model="gpt-4o",
        temperature=0.2,
        openai_api_base="http://custom.endpoint/v1",
        api_key="not-needed",
    )
