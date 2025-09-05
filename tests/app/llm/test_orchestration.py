import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AuthenticationError

import json
from resume_editor.app.llm.orchestration import (
    _get_section_content,
    _refine_experience_section,
    _refine_generic_section,
    analyze_job_description,
    refine_experience_section,
    refine_resume_section_with_llm,
    refine_role,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.llm.models import JobAnalysis, RefinedSection
from resume_editor.app.models.resume.experience import (
    Project,
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)

FULL_RESUME = """# Personal
name: Test Person

# Education
school: Test University

# Experience
company: Test Company

# Certifications
name: Test Cert
"""


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


@pytest.mark.parametrize(
    "section_name, extractor, serializer, expected_output",
    [
        (
            "personal",
            "extract_personal_info",
            "serialize_personal_info_to_markdown",
            "personal section",
        ),
        (
            "education",
            "extract_education_info",
            "serialize_education_to_markdown",
            "education section",
        ),
        (
            "experience",
            "extract_experience_info",
            "serialize_experience_to_markdown",
            "experience section",
        ),
        (
            "certifications",
            "extract_certifications_info",
            "serialize_certifications_to_markdown",
            "certifications section",
        ),
    ],
)
def test_get_section_content(section_name, extractor, serializer, expected_output):
    """Test that _get_section_content correctly calls extract and serialize for each section."""
    with (
        patch(
            f"resume_editor.app.llm.orchestration.{extractor}",
        ) as mock_extract,
        patch(
            f"resume_editor.app.llm.orchestration.{serializer}",
            return_value=expected_output,
        ) as mock_serialize,
    ):
        result = _get_section_content(FULL_RESUME, section_name)

        mock_extract.assert_called_once_with(FULL_RESUME)
        mock_serialize.assert_called_once_with(mock_extract.return_value)
        assert result == expected_output


def test_get_section_content_full():
    """Test that _get_section_content returns the full resume for 'full' section."""
    assert _get_section_content(FULL_RESUME, "full") == FULL_RESUME


def test_get_section_content_invalid():
    """Test that _get_section_content raises ValueError for an invalid section."""
    with pytest.raises(ValueError, match="Invalid section name: invalid"):
        _get_section_content(FULL_RESUME, "invalid")


@pytest.mark.asyncio
async def test_analyze_job_description_empty_input():
    """Test that analyze_job_description raises ValueError for empty input."""
    with pytest.raises(ValueError, match="Job description cannot be empty."):
        await analyze_job_description(
            job_description=" ",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@patch("resume_editor.app.llm.orchestration._get_section_content")
def test_refine_generic_section_empty_section(mock_get_section):
    """Test that the LLM is not called for an empty resume section."""
    mock_get_section.return_value = "  "
    # We pass a mock LLM because the function being tested doesn't create one.
    mock_llm = MagicMock()
    result = _refine_generic_section(
        "resume", "job desc", "personal", llm=mock_llm
    )
    assert result == ""
    mock_get_section.assert_called_once_with("resume", "personal")
    # The LLM's chain should not be invoked.
    mock_llm.invoke.assert_not_called()


@pytest.fixture
def mock_chain_invocations_for_analysis():
    """
    Fixture to mock the LangChain chain invocation for job analysis.
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

        # Mock the `|` operator chaining
        prompt_llm_chain = MagicMock()
        mock_prompt_partial.__or__.return_value = prompt_llm_chain

        final_chain = MagicMock()
        prompt_llm_chain.__or__.return_value = final_chain

        # The final ainvoke should return a string, not a JobAnalysis object
        final_chain.ainvoke = AsyncMock(
            return_value='```json\n{"required_skills": ["python", "fastapi"], "nice_to_have_skills": ["docker"], "job_title": "Software Engineer"}\n```'
        )

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@pytest.mark.asyncio
async def test_analyze_job_description(mock_chain_invocations_for_analysis):
    """Test that analyze_job_description returns a valid JobAnalysis object."""
    result = await analyze_job_description(
        job_description="some job description",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )
    assert isinstance(result, JobAnalysis)
    assert result.required_skills == ["python", "fastapi"]
    assert result.nice_to_have_skills == ["docker"]
    assert result.job_title == "Software Engineer"


def test_refine_resume_section_with_llm_dispatcher():
    """Test that the refine_resume_section_with_llm dispatcher calls the correct helper."""
    with patch(
        "resume_editor.app.llm.orchestration._refine_generic_section"
    ) as mock_refine_generic, patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class:
        mock_refine_generic.return_value = "refined content from helper"
        result = refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )
        assert result == "refined content from helper"
        mock_chat_openai_class.assert_called_once()
        mock_refine_generic.assert_called_once()


@pytest.mark.parametrize("llm_endpoint, api_key, llm_model_name, expected_call_args", LLM_INIT_PARAMS)
@pytest.mark.asyncio
async def test_analyze_job_description_llm_initialization(
    mock_chain_invocations_for_analysis,
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters for analysis.
    """
    await analyze_job_description(
        job_description="some job description",
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    mock_chat_openai = mock_chain_invocations_for_analysis["chat_openai"]
    mock_chat_openai.assert_called_once_with(**expected_call_args)


@pytest.mark.asyncio
async def test_analyze_job_description_json_decode_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that a JSONDecodeError from the LLM call is handled gracefully in analysis.
    """
    import json

    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.side_effect = json.JSONDecodeError(
        "Expecting value", "invalid json", 0
    )

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_validation_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that a Pydantic validation error is handled gracefully in analysis.
    """
    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.return_value = '```json\n{"wrong_field": "wrong_value"}\n```'

    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_authentication_error(
    mock_chain_invocations_for_analysis,
):
    """
    Test that an AuthenticationError from the LLM call is propagated during analysis.
    """
    from openai import AuthenticationError

    final_chain = mock_chain_invocations_for_analysis["final_chain"]
    final_chain.ainvoke.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )

    with pytest.raises(AuthenticationError):
        await analyze_job_description(
            job_description="job desc",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


@pytest.mark.asyncio
async def test_analyze_job_description_prompt_content(
    mock_chain_invocations_for_analysis,
):
    """Test that the prompt for analyze_job_description is constructed correctly."""
    # Act
    await analyze_job_description(
        job_description="A job description",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )

    # Assert
    mock_prompt_template = mock_chain_invocations_for_analysis["prompt_template"]
    mock_prompt_from_messages = mock_chain_invocations_for_analysis[
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
    assert "As a professional resume writer and career coach" in system_template
    assert "{format_instructions}" in system_template
    assert "{job_description}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "format_instructions" in partial_kwargs


@pytest.fixture
def mock_get_section_content():
    """Fixture to mock _get_section_content."""
    with patch(
        "resume_editor.app.llm.orchestration._get_section_content"
    ) as mock:
        mock.return_value = "some resume section"
        yield mock


@pytest.fixture
def mock_chain_invocations():
    """
    Fixture to mock the entire LangChain chain invocation process.
    It patches the key components and mocks the `|` operator to
    ensure the final `chain.invoke` call returns a valid object.
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

        # Mock the `|` operator chaining
        prompt_llm_chain = MagicMock()
        mock_prompt_partial.__or__.return_value = prompt_llm_chain

        final_chain = MagicMock()
        prompt_llm_chain.__or__.return_value = final_chain

        # The final invoke should return a string, not a RefinedSection object
        final_chain.invoke.return_value = (
            '```json\n{"refined_markdown": "refined content"}\n```'
        )

        yield {
            "chat_openai": mock_chat_openai_class,
            "final_chain": final_chain,
            "prompt_template": mock_prompt_template_class,
            "prompt_from_messages": mock_prompt_from_messages,
        }


@pytest.mark.parametrize("llm_endpoint, api_key, llm_model_name, expected_call_args", LLM_INIT_PARAMS)
def test_refine_resume_section_with_llm_initialization(
    llm_endpoint,
    api_key,
    llm_model_name,
    expected_call_args,
):
    """
    Test that ChatOpenAI is initialized with the correct parameters under various conditions
    and that the helper function is called.
    """
    with patch(
        "resume_editor.app.llm.orchestration._refine_generic_section"
    ) as mock_refine_helper, patch(
        "resume_editor.app.llm.orchestration.ChatOpenAI"
    ) as mock_chat_openai_class:
        # Mock the LLM object that will be created
        mock_llm_instance = MagicMock()
        mock_chat_openai_class.return_value = mock_llm_instance

        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        )

        # Assert ChatOpenAI was initialized correctly
        mock_chat_openai_class.assert_called_once_with(**expected_call_args)

        # Assert helper was called with the created LLM instance
        mock_refine_helper.assert_called_once_with(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm_instance,
        )


def test_refine_generic_section_json_decode_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section handles a JSONDecodeError from the LLM call gracefully.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.side_effect = json.JSONDecodeError(
        "Expecting value", "some invalid json", 0
    )
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )


def test_refine_generic_section_validation_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section handles a Pydantic validation error gracefully.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.return_value = '```json\n{"wrong_field": "wrong_value"}\n```'
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(
        ValueError,
        match="The AI service returned an unexpected response. Please try again.",
    ):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )


def test_refine_generic_section_authentication_error(
    mock_chain_invocations, mock_get_section_content
):
    """
    Test that _refine_generic_section propagates an AuthenticationError from the LLM call.
    """
    # Arrange
    final_chain = mock_chain_invocations["final_chain"]
    final_chain.invoke.side_effect = AuthenticationError(
        message="Invalid API key", response=MagicMock(), body=None
    )
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act & Assert
    with pytest.raises(AuthenticationError):
        _refine_generic_section(
            resume_content="resume",
            job_description="job desc",
            target_section="personal",
            llm=mock_llm,
        )


@pytest.mark.parametrize(
    "target_section, expect_guidelines",
    [
        ("personal", False),
        ("education", False),
        ("certifications", False),
        ("full", False),
    ],
)
def test_refine_generic_section_prompt_content(
    target_section,
    expect_guidelines,
    mock_chain_invocations,
    mock_get_section_content,
):
    """
    Test that the prompt for _refine_generic_section is constructed correctly.
    """
    # Arrange
    mock_llm = mock_chain_invocations["chat_openai"].return_value

    # Act
    _refine_generic_section(
        resume_content="resume",
        job_description="job desc",
        target_section=target_section,
        llm=mock_llm,
    )

    # Assert
    mock_prompt_template = mock_chain_invocations["prompt_template"]
    mock_prompt_from_messages = mock_chain_invocations["prompt_from_messages"]

    # Check that from_messages was called with system and human templates
    mock_prompt_template.from_messages.assert_called_once()
    messages = mock_prompt_template.from_messages.call_args.args[0]
    assert messages[0][0] == "system"
    assert messages[1][0] == "human"

    system_template = messages[0][1]
    human_template = messages[1][1]

    # Check that crucial rules and spec are always in the system template
    assert "MARKDOWN RESUME SPECIFICATION EXAMPLE" in system_template
    assert "Stick to the Facts" in system_template

    # Check that placeholders are in the templates
    assert "{goal}" in system_template
    assert "{processing_guidelines}" in system_template
    assert "{job_description}" in human_template
    assert "{resume_section}" in human_template

    # Check the content passed to partial()
    mock_prompt_from_messages.partial.assert_called_once()
    partial_kwargs = mock_prompt_from_messages.partial.call_args.kwargs
    assert "Rephrase and restructure" in partial_kwargs["goal"]

    if expect_guidelines:
        assert "**Processing Guidelines:**" in partial_kwargs["processing_guidelines"]
        assert "For each `### Role`" in partial_kwargs["processing_guidelines"]
    else:
        assert partial_kwargs["processing_guidelines"] == ""


def test_refine_resume_section_with_llm_experience_raises_error():
    """
    Test that refine_resume_section_with_llm raises an error for 'experience' section.
    """
    with pytest.raises(
        ValueError,
        match="Experience section refinement must be called via the async 'refine_experience_section' method.",
    ):
        refine_resume_section_with_llm(
            resume_content="resume",
            job_description="job desc",
            target_section="experience",
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


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
        required_skills=["python", "fastapi"],
        nice_to_have_skills=["docker"],
        job_title="Software Engineer",
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
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )

    assert isinstance(result, Role)
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
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
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
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


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
            llm_endpoint=None,
            api_key=None,
            llm_model_name=None,
        )


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
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    mock_chat_openai = mock_chain_invocations_for_role_refine["chat_openai"]
    mock_chat_openai.assert_called_once_with(**expected_call_args)


@pytest.mark.asyncio
async def test_refine_role_prompt_content(mock_chain_invocations_for_role_refine):
    """Test that the prompt for refine_role is constructed correctly."""
    # Act
    await refine_role(
        role=create_mock_role(),
        job_analysis=create_mock_job_analysis(),
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
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


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration._refine_experience_section")
async def test_refine_experience_section_wrapper_success(mock_private_refiner):
    """Test that the public refine_experience_section wrapper correctly calls and yields from the private generator."""
    # Arrange
    async def mock_generator():
        yield {"status": "one"}
        yield {"status": "two"}

    mock_private_refiner.return_value = mock_generator()

    # Act
    events = []
    async for event in refine_experience_section("r", "j", None, None, None):
        events.append(event)

    # Assert
    mock_private_refiner.assert_called_once_with(
        resume_content="r",
        job_description="j",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    )
    assert events == [{"status": "one"}, {"status": "two"}]


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.reconstruct_resume_markdown")
@patch("resume_editor.app.llm.orchestration.refine_role")
@patch("resume_editor.app.llm.orchestration.analyze_job_description")
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.llm.orchestration.extract_certifications_info")
@patch("resume_editor.app.llm.orchestration.extract_education_info")
@patch("resume_editor.app.llm.orchestration.extract_personal_info")
async def test__refine_experience_section(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_certifications,
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
    mock_reconstruct,
):
    """Test that the async orchestrator yields correct statuses and final content."""
    # Arrange
    # 1. Mock inputs
    resume_content = "full resume markdown"
    job_description = "the best job ever"
    llm_endpoint = "http://fake.llm"
    api_key = "fake_key"
    llm_model_name = "fake-model"

    # 2. Mock return values for extractors
    mock_personal_info = PersonalInfoResponse(name="Test Person")
    mock_education_info = EducationResponse(degrees=[])
    mock_certifications_info = CertificationsResponse(certifications=[])

    original_role1 = create_mock_role()
    original_role1.basics.company = "Company 1"
    original_role2 = create_mock_role()
    original_role2.basics.company = "Company 2"
    mock_projects = [MagicMock(spec=Project)]  # Safely mock projects

    mock_experience_info = ExperienceResponse(
        roles=[original_role1, original_role2], projects=mock_projects
    )

    mock_extract_personal.return_value = mock_personal_info
    mock_extract_education.return_value = mock_education_info
    mock_extract_certifications.return_value = mock_certifications_info
    mock_extract_experience.return_value = mock_experience_info

    # 3. Mock return value for job analyzer (it's called with await)
    mock_job_analysis = create_mock_job_analysis()
    mock_analyze_job.return_value = mock_job_analysis

    # 4. Mock return values for refiner (it's called with await)
    refined_role1 = create_mock_role()
    refined_role1.summary.text = "Refined summary 1"
    refined_role2 = create_mock_role()
    refined_role2.summary.text = "Refined summary 2"
    mock_refine_role.side_effect = [refined_role1, refined_role2]

    # 5. Mock return value for reconstructor
    final_markdown = "final reconstructed markdown"
    mock_reconstruct.return_value = final_markdown

    # Act
    events = []
    async for event in _refine_experience_section(
        resume_content=resume_content,
        job_description=job_description,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    ):
        events.append(event)

    # Assert
    # 1. Check yielded events
    assert events == [
        {"status": "Parsing resume..."},
        {"status": "Analyzing job description..."},
        {"status": "Refining role 1 of 2"},
        {"status": "Refining role 2 of 2"},
        {"status": "Reconstructing resume..."},
        {"status": "done", "content": final_markdown},
    ]

    # 2. Check mocks were called
    mock_analyze_job.assert_awaited_once_with(
        job_description=job_description,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    assert mock_refine_role.await_count == 2
    mock_refine_role.assert_any_call(
        role=original_role1,
        job_analysis=mock_job_analysis,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )
    mock_refine_role.assert_any_call(
        role=original_role2,
        job_analysis=mock_job_analysis,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )

    mock_reconstruct.assert_called_once()
    reconstruct_kwargs = mock_reconstruct.call_args.kwargs
    assert reconstruct_kwargs["experience"].roles == [refined_role1, refined_role2]


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.reconstruct_resume_markdown")
@patch("resume_editor.app.llm.orchestration.refine_role")
@patch("resume_editor.app.llm.orchestration.analyze_job_description")
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.llm.orchestration.extract_certifications_info")
@patch("resume_editor.app.llm.orchestration.extract_education_info")
@patch("resume_editor.app.llm.orchestration.extract_personal_info")
async def test__refine_experience_section_no_roles(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_certifications,
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
    mock_reconstruct,
):
    """Test that the orchestrator handles resumes with no roles in the experience section."""
    # Arrange
    mock_extract_personal.return_value = PersonalInfoResponse(name="Test Person")
    mock_extract_education.return_value = EducationResponse(degrees=[])
    mock_extract_certifications.return_value = CertificationsResponse(
        certifications=[]
    )
    mock_projects = [MagicMock(spec=Project)]
    mock_experience_info = ExperienceResponse(roles=[], projects=mock_projects)
    mock_extract_experience.return_value = mock_experience_info

    mock_job_analysis = create_mock_job_analysis()
    mock_analyze_job.return_value = mock_job_analysis
    mock_reconstruct.return_value = "reconstructed content with no roles"

    # Act
    events = []
    async for event in _refine_experience_section(
        resume_content="some content",
        job_description="some job",
        llm_endpoint=None,
        api_key=None,
        llm_model_name=None,
    ):
        events.append(event)

    # Assert
    # 1. Check yielded events
    assert events == [
        {"status": "Parsing resume..."},
        {"status": "Analyzing job description..."},
        {"status": "Reconstructing resume..."},
        {"status": "done", "content": "reconstructed content with no roles"},
    ]

    # 2. Check mocks were called
    mock_analyze_job.assert_awaited_once()
    mock_refine_role.assert_not_called()
    mock_reconstruct.assert_called_once()
    reconstruct_kwargs = mock_reconstruct.call_args.kwargs
    assert reconstruct_kwargs["experience"].roles == []
    assert reconstruct_kwargs["experience"].projects == mock_projects


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.extract_personal_info")
@patch("resume_editor.app.llm.orchestration.extract_education_info")
@patch("resume_editor.app.llm.orchestration.extract_certifications_info")
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.llm.orchestration.analyze_job_description")
async def test__refine_experience_section_job_analysis_fails(
    mock_analyze_job,
    mock_extract_experience,
    mock_extract_certifications,
    mock_extract_education,
    mock_extract_personal,
):
    """Test private orchestrator raises error if job analysis fails."""
    # Arrange
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_extract_experience.return_value = MagicMock()
    mock_analyze_job.side_effect = ValueError("Job analysis failed")

    # Act & Assert
    events = []
    with pytest.raises(ValueError, match="Job analysis failed"):
        async for event in _refine_experience_section(
            "resume", "job", None, None, None
        ):
            events.append(event)

    assert events == [
        {"status": "Parsing resume..."},
        {"status": "Analyzing job description..."},
    ]


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.reconstruct_resume_markdown")
@patch("resume_editor.app.llm.orchestration.refine_role")
@patch("resume_editor.app.llm.orchestration.analyze_job_description")
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.llm.orchestration.extract_certifications_info")
@patch("resume_editor.app.llm.orchestration.extract_education_info")
@patch("resume_editor.app.llm.orchestration.extract_personal_info")
async def test__refine_experience_section_role_refinement_fails(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_certifications,
    mock_extract_experience,
    mock_analyze_job,
    mock_refine_role,
    mock_reconstruct,
):
    """Test that the private orchestrator raises an error if role refinement fails."""
    # Arrange: Let the first role refinement fail
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_certifications.return_value = MagicMock()
    mock_refine_role.side_effect = ValueError("Role refinement failed")

    original_role1 = create_mock_role()
    mock_experience_info = ExperienceResponse(roles=[original_role1], projects=[])
    mock_extract_experience.return_value = mock_experience_info
    mock_analyze_job.return_value = create_mock_job_analysis()

    # Act & Assert
    events = []
    with pytest.raises(ValueError, match="Role refinement failed"):
        async for event in _refine_experience_section(
            "resume", "job", None, None, None
        ):
            events.append(event)

    # Assert
    assert events == [
        {"status": "Parsing resume..."},
        {"status": "Analyzing job description..."},
        {"status": "Refining role 1 of 1"},
    ]
    mock_analyze_job.assert_awaited_once()
    mock_refine_role.assert_awaited_once()
    mock_reconstruct.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.log")
@patch("resume_editor.app.llm.orchestration._refine_experience_section")
async def test_refine_experience_section_wrapper_general_exception(
    mock_private_refiner, mock_log
):
    """Test that the public wrapper handles a general exception from the private generator."""
    # Arrange
    async def mock_generator_with_error():
        yield {"status": "one"}
        raise Exception("A wild error appeared!")

    mock_private_refiner.return_value = mock_generator_with_error()

    # Act
    events = []
    async for event in refine_experience_section("r", "j", None, None, None):
        events.append(event)

    # Assert
    assert len(events) == 2
    assert events[0] == {"status": "one"}
    assert events[1] == {"status": "error", "message": "A wild error appeared!"}
    mock_log.exception.assert_called_once()
    assert "An unexpected error occurred" in mock_log.exception.call_args.args[0]


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.log")
@patch("resume_editor.app.llm.orchestration._refine_experience_section")
async def test_refine_experience_section_wrapper_authentication_error(
    mock_private_refiner, mock_log
):
    """Test that the public wrapper handles an AuthenticationError from the private generator."""
    # Arrange
    async def mock_generator_with_auth_error():
        yield {"status": "one"}
        raise AuthenticationError("Invalid key", response=MagicMock(), body=None)

    mock_private_refiner.return_value = mock_generator_with_auth_error()

    # Act
    events = []
    async for event in refine_experience_section("r", "j", None, None, None):
        events.append(event)

    # Assert
    assert len(events) == 2
    assert events[0] == {"status": "one"}
    assert events[1] == {
        "status": "error",
        "message": "LLM authentication failed. Please check your API key in settings.",
    }
    mock_log.warning.assert_called_once()
    assert "LLM authentication error" in mock_log.warning.call_args.args[0]
