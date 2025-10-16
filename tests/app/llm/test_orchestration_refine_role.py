from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AuthenticationError

import json

from resume_editor.app.llm.orchestration import refine_role
from resume_editor.app.llm.models import JobAnalysis, LLMConfig, RefinedRole
from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)


LLM_INIT_PARAMS = [
    # Case 1: Endpoint, API key, and model name provided
    (
        "http://fake.llm",
        "key",
        "custom-model",
        {
            "model": "custom-model",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 2: Endpoint and model name, but no API key (should use dummy key)
    (
        "http://fake.llm",
        None,
        "custom-model",
        {
            "model": "custom-model",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "not-needed",
        },
    ),
    # Case 3: API key and model name, but no endpoint
    (
        None,
        "key",
        "custom-model",
        {"model": "custom-model", "temperature": 0.7, "api_key": "key"},
    ),
    # Case 4: No endpoint, no API key (relies on env var)
    (
        None,
        None,
        "custom-model",
        {"model": "custom-model", "temperature": 0.7},
    ),
    # Case 5: Fallback to default model name when None is provided
    (
        "http://fake.llm",
        "key",
        None,
        {
            "model": "gpt-4o",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 6: Fallback to default model name when empty string is provided
    (
        "http://fake.llm",
        "key",
        "",
        {
            "model": "gpt-4o",
            "temperature": 0.7,
            "openai_api_base": "http://fake.llm",
            "api_key": "key",
        },
    ),
    # Case 7: OpenRouter endpoint with API key
    (
        "https://openrouter.ai/api/v1",
        "or-key",
        "openrouter/model",
        {
            "model": "openrouter/model",
            "temperature": 0.7,
            "openai_api_base": "https://openrouter.ai/api/v1",
            "api_key": "or-key",
            "default_headers": {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            },
        },
    ),
]


def create_mock_role() -> Role:
    """Helper to create a mock Role object for testing."""
    return Role(
        basics=RoleBasics(
            company="Old Company",
            title="Old Title",
            start_date=datetime(2020, 1, 1),
        ),
        summary=RoleSummary(text="Old summary."),
        responsibilities=RoleResponsibilities(text="* Do old things."),
        skills=RoleSkills(skills=["Old Skill"]),
    )


def create_mock_job_analysis() -> JobAnalysis:
    """Helper to create a mock JobAnalysis object for testing."""
    return JobAnalysis(
        key_skills=["python", "fastapi"],
        primary_duties=["develop things"],
        themes=["agile"],
    )


@pytest.fixture
def mock_chain_invocations_for_role_refine():
    """
    Fixture to mock the LangChain chain invocation for role refinement.
    """
    with patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class, patch(
        "resume_editor.app.llm.orchestration.ChatPromptTemplate"
    ) as mock_prompt_template_class, patch(
        "resume_editor.app.llm.orchestration.PydanticOutputParser"
    ), patch(
        "resume_editor.app.llm.orchestration.StrOutputParser"
    ):
        mock_prompt_from_messages = MagicMock()
        mock_prompt_template_class.from_messages.return_value = (
            mock_prompt_from_messages
        )

        mock_prompt_partial = MagicMock()
        mock_prompt_from_messages.partial.return_value = mock_prompt_partial

        prompt_llm_chain = MagicMock()
        mock_prompt_partial.__or__.return_value = prompt_llm_chain

        final_chain = MagicMock()
        prompt_llm_chain.__or__.return_value = final_chain

        # The final invoke should return a JSON string representing a refined Role
        refined_role_dict = {
            "basics": {
                "company": "Old Company",
                "start_date": "2020-01-01T00:00:00",
                "end_date": None,
                "title": "Old Title",
                "reason_for_change": None,
                "location": None,
                "job_category": None,
                "employment_type": None,
                "agency_name": None,
                "inclusion_status": "Include",
            },
            "summary": {"text": "Refined summary."},
            "responsibilities": {"text": "* Do refined things."},
            "skills": {"skills": ["Refined Skill"]},
        }

        final_chain.ainvoke = AsyncMock(
            return_value=f"```json\n{json.dumps(refined_role_dict)}\n```"
        )

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@pytest.mark.asyncio
async def test_refine_role_success(mock_chain_invocations_for_role_refine):
    """Test the successful refinement of a Role object."""
    mock_role = create_mock_role()
    mock_job_analysis = create_mock_job_analysis()

    result = await refine_role(
        role=mock_role,
        job_analysis=mock_job_analysis,
        llm_config=LLMConfig(),
    )

    assert isinstance(result, RefinedRole)
    assert result.summary.text == "Refined summary."
    assert result.responsibilities.text == "* Do refined things."
    assert result.skills.skills == ["Refined Skill"]

    # Check that the input objects were correctly serialized and passed to the chain
    final_chain = mock_chain_invocations_for_role_refine["final_chain"]
    final_chain.ainvoke.assert_called_once()
    invoke_args = final_chain.ainvoke.call_args.args[0]

    assert invoke_args["role_json"] == mock_role.model_dump_json(indent=2)
    assert (
        invoke_args["job_analysis_json"]
        == mock_job_analysis.model_dump_json(indent=2)
    )


@pytest.mark.asyncio
async def test_refine_role_json_error(mock_chain_invocations_for_role_refine):
    """Test that refine_role handles JSON decoding errors."""
    final_chain = mock_chain_invocations_for_role_refine["final_chain"]
    final_chain.ainvoke.return_value = "```json\n{ not valid json }\n```"

    with pytest.raises(ValueError, match="unexpected response"):
        await refine_role(
            role=create_mock_role(),
            job_analysis=create_mock_job_analysis(),
            llm_config=LLMConfig(),
        )


@pytest.mark.asyncio
async def test_refine_role_validation_error(mock_chain_invocations_for_role_refine):
    """Test that refine_role handles Pydantic validation errors."""
    final_chain = mock_chain_invocations_for_role_refine["final_chain"]
    # Return valid JSON but with missing required fields within the "basics" object.
    final_chain.ainvoke.return_value = '```json\n{"basics": {"company": "foo"}}\n```'

    with pytest.raises(ValueError, match="unexpected response"):
        await refine_role(
            role=create_mock_role(),
            job_analysis=create_mock_job_analysis(),
            llm_config=LLMConfig(),
        )


@pytest.mark.asyncio
async def test_refine_role_prompt_content(mock_chain_invocations_for_role_refine):
    """Test that the prompt for refine_role is constructed correctly."""
    # Act
    await refine_role(
        role=create_mock_role(),
        job_analysis=create_mock_job_analysis(),
        llm_config=LLMConfig(),
    )

    # Assert
    mock_prompt_template = mock_chain_invocations_for_role_refine["prompt_template"]
    mock_prompt_from_messages = mock_chain_invocations_for_role_refine[
        "prompt_from_messages"
    ]

    # Check that from_messages was called with system and human templates
    mock_prompt_template.from_messages.assert_called_once()
    messages = mock_prompt_template.from_messages.call_args.args[0]
    assert messages[0][0] == "system"
    assert messages[1][0] == "human"

    system_template = messages[0][1]
    human_template = messages[1][1]

    # Check that crucial rules and spec are always in the system template
    assert "As an expert resume writer" in system_template
    assert (
        "your task is to refine the provided `role` JSON object" in system_template
    )
    assert "{format_instructions}" in system_template
    assert "Role to Refine:" in human_template
    assert "Job Analysis (for context):" in human_template
    assert "{role_json}" in human_template
    assert "{job_analysis_json}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "format_instructions" in partial_kwargs


@pytest.mark.parametrize("llm_endpoint, api_key, llm_model_name, expected_call_args", LLM_INIT_PARAMS)
@pytest.mark.asyncio
async def test_refine_role_llm_initialization(
    mock_chain_invocations_for_role_refine,
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters for role refinement.
    """
    await refine_role(
        role=create_mock_role(),
        job_analysis=create_mock_job_analysis(),
        llm_config=LLMConfig(
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        ),
    )
    mock_chat_openai = mock_chain_invocations_for_role_refine["chat_openai"]
    mock_chat_openai.assert_called_once_with(**expected_call_args)


@pytest.mark.asyncio
async def test_refine_role_authentication_error(
    mock_chain_invocations_for_role_refine,
):
    """
    Test that an AuthenticationError from the LLM call is propagated during role refinement.
    """
    from openai import AuthenticationError

    final_chain = mock_chain_invocations_for_role_refine["final_chain"]
    final_chain.ainvoke.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )

    with pytest.raises(AuthenticationError):
        await refine_role(
            role=create_mock_role(),
            job_analysis=create_mock_job_analysis(),
            llm_config=LLMConfig(),
        )
