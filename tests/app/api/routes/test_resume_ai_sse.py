from unittest.mock import AsyncMock, MagicMock, Mock, patch
import logging
import asyncio
import pytest
from cryptography.fernet import InvalidToken
from openai import AuthenticationError

from resume_editor.app.models.user_settings import UserSettings


VALID_RESUME_TWO_ROLES = """# Personal

## Contact Information

Name: Test Person

# Education

## Degrees

### Degree

School: A School

# Certifications

## Certification

Name: A Cert

# Experience

## Roles

### Role

#### Basics

Company: A Company
Title: A Role
Start date: 01/2024

### Role

#### Basics

Company: B Company
Title: B Role
Start date: 01/2023

## Projects

### Project

#### Overview

Title: A Cool Project
#### Description

A project description.
"""


_real_asyncio_sleep = asyncio.sleep


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch(
    "resume_editor.app.api.routes.resume_ai.decrypt_data",
    return_value="decrypted_key",
)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_happy_path(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_refine_result_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test successful SSE refinement via the new GET stream endpoint."""
    # This test mocks the orchestrator, so the original resume content just needs
    # to be consistent for the reconstruction step.
    test_resume.content = VALID_RESUME_TWO_ROLES

    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectOverview,
        Role,
        RoleBasics,
        RoleSummary,
    )

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings

    # Mock extractors to return valid data, including projects
    mock_project = Project(overview=ProjectOverview(title="A Cool Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = MagicMock()
    mock_build_sections.return_value = "reconstructed content"

    # Mock the async generator from refine_experience_section
    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump(mode="json")
    refined_role2 = Role(
        basics=RoleBasics(
            company="Refined Company 2",
            title="Refined Role 2",
            start_date="2023-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 2"),
    )
    refined_role2_data = refined_role2.model_dump(mode="json")

    async def mock_async_generator():
        yield {"status": "in_progress", "message": "doing stuff"}
        yield {"status": "introduction_generated", "data": "Generated Intro"}
        # Yield out of order to ensure sorting logic is tested
        yield {
            "status": "role_refined",
            "data": refined_role2_data,
            "original_index": 1,
        }
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_create_refine_result_html.return_value = "<html>final refined html</html>"

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")
    # Expected: progress, introduction, done, close
    assert len(events) == 4, f"Expected 4 events, got {len(events)}: {events}"

    assert "event: progress" in events[0]
    assert "data: <li>doing stuff</li>" in events[0]
    assert "event: introduction_generated" in events[1]
    assert 'id="introduction-container"' in events[1]
    assert "event: done" in events[2]
    assert "data: <html>final refined html</html>" in events[2]
    assert "event: close" in events[3]

    # Assert mocks
    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=True,
    )
    mock_extract_personal.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_education.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_experience.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_extract_certifications.assert_called_once_with(VALID_RESUME_TWO_ROLES)
    mock_build_sections.assert_called_once()
    reconstruct_kwargs = mock_build_sections.call_args.kwargs
    reconstructed_experience = reconstruct_kwargs["experience"]
    reconstructed_roles = reconstructed_experience.roles

    assert len(reconstructed_roles) == 2
    assert reconstructed_roles[0].summary.text == "Refined Summary 1"
    assert reconstructed_roles[1].summary.text == "Refined Summary 2"
    assert reconstructed_experience.projects == mock_original_experience.projects

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated Intro",
    )

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated Intro",
    )


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch(
    "resume_editor.app.api.routes.resume_ai.decrypt_data",
    return_value="decrypted_key",
)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_happy_path_gen_intro_false(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_refine_result_html,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """Test successful SSE refinement when generate_introduction is false."""
    test_resume.content = VALID_RESUME_TWO_ROLES

    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectOverview,
        Role,
        RoleBasics,
        RoleSummary,
    )

    mock_settings = UserSettings(
        user_id=test_user.id,
        llm_endpoint="http://llm.test",
        encrypted_api_key="key",
        llm_model_name="test-model",
    )
    mock_get_user_settings.return_value = mock_settings

    mock_project = Project(overview=ProjectOverview(title="A Cool Project"))
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_experience.return_value = mock_original_experience
    mock_build_sections.return_value = "reconstructed content"

    refined_role1 = Role(
        basics=RoleBasics(
            company="Refined Company 1",
            title="Refined Role 1",
            start_date="2024-01-01",
        ),
        summary=RoleSummary(text="Refined Summary 1"),
    )
    refined_role1_data = refined_role1.model_dump(mode="json")

    async def mock_async_generator():
        yield {
            "status": "role_refined",
            "data": refined_role1_data,
            "original_index": 0,
        }

    mock_async_refine_experience.return_value = mock_async_generator()
    mock_create_refine_result_html.return_value = "<html>final refined html</html>"

    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=false",
    ) as response:
        assert response.status_code == 200

    mock_async_refine_experience.assert_called_once_with(
        resume_content=VALID_RESUME_TWO_ROLES,
        job_description="a new job",
        llm_endpoint="http://llm.test",
        api_key="decrypted_key",
        llm_model_name="test-model",
        generate_introduction=False,
    )

    mock_create_refine_result_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction=None,
    )


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_introduction_is_none(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test that an introduction_generated event with None data is handled."""

    async def mock_generator():
        yield {"status": "introduction_generated", "data": None}
        yield {"status": "in_progress", "message": "doing stuff"}

    mock_async_refine_experience.return_value = mock_generator()

    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")

    # The empty introduction event should be ignored.
    # The stream continues and since no roles are refined, it sends an error.
    # Expected events: progress, error (since no roles are refined), and close.
    assert len(events) == 3
    assert "event: progress" in events[0]
    assert "data: <li>doing stuff</li>" in events[0]
    assert "event: error" in events[1]
    assert "Refinement finished, but no roles were found to refine." in events[1]
    assert "event: close" in events[2]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_orchestration_error(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test that an error raised by the orchestrator is handled in the SSE stream."""

    # Mock the async generator to raise an error
    mock_async_refine_experience.side_effect = ValueError("Orchestration failed")

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2  # error event, and close event

    error_event = events[0]
    assert "event: error" in error_event
    assert (
        "data: <div role='alert' class='text-red-500 p-2'>Refinement failed: Orchestration failed</div>"
        in error_event
    )

    close_event = events[1]
    assert "event: close" in close_event
    assert "data: stream complete" in close_event

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed_event",
    [
        {"status": "processing", "message": "unhandled status"},  # Unknown status
        {"status": "role_refined", "data": {"some": "data"}},  # Missing index
        {"status": "role_refined", "original_index": 0},  # Missing data
        {"status": "role_refined", "data": None, "original_index": 0},
        {"status": "role_refined", "data": {"some": "data"}, "original_index": None},
    ],
)
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_malformed_events(
    mock_get_user_settings,
    mock_async_refine_experience,
    malformed_event,
    client_with_auth_and_resume,
):
    """Test SSE stream handles unknown or malformed events gracefully."""

    async def mock_async_generator():
        yield malformed_event

    mock_async_refine_experience.return_value = mock_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    # The generator should not add any roles, so an error event for "no roles"
    # should be yielded, followed by the close event.
    events = text_content.strip().split("\n\n")
    assert len(events) == 2, f"Expected 2 events, got {len(events)}: {events}"
    assert "event: error" in events[0]
    assert "Refinement finished, but no roles were found to refine." in events[0]
    assert "text-yellow-500" in events[0]
    assert "event: close" in events[1]

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_empty_generator(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test SSE stream with an empty generator from the LLM service."""

    # Mock the async generator to be empty
    async def mock_empty_async_generator():
        return
        yield  # pylint: disable=unreachable

    mock_async_refine_experience.return_value = mock_empty_async_generator()

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2, f"Expected 2 events, but got {len(events)}: {events}"
    assert "event: error" in events[0]
    assert "Refinement finished, but no roles were found to refine." in events[0]
    assert "text-yellow-500" in events[0]
    assert "event: close" in events[1]

    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.llm.orchestration.analyze_job_description", new_callable=AsyncMock)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_no_roles_in_resume(
    mock_get_user_settings,
    mock_analyze_job,
    client_with_auth_and_resume,
    test_resume,
):
    """Test SSE stream when the resume has no roles in the experience section."""
    from resume_editor.app.llm.models import JobAnalysis

    # Arrange
    resume_with_no_roles = """# Personal
Name: Test

# Experience
## Projects
### Project
#### Overview
Title: A project
#### Description
A project with no roles.
"""
    test_resume.content = resume_with_no_roles
    mock_analyze_job.return_value = (
        JobAnalysis(key_skills=[], primary_duties=[], themes=[]),
        None,
    )

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")
    assert len(events) == 4, f"Expected 4 events, got {len(events)}: {events}"

    assert "event: progress" in events[0] and "Parsing resume..." in events[0]
    assert "event: progress" in events[1] and "Analyzing job description..." in events[1]
    assert "event: error" in events[2]
    # This message comes from sse_generator when refined_roles is empty.
    # The orchestrator returns early in this case, leading to an empty refined_roles dict.
    assert "Refinement finished, but no roles were found to refine" in events[2]
    assert "text-yellow-500" in events[2]
    assert "event: close" in events[3]
    mock_analyze_job.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.decrypt_data", side_effect=InvalidToken)
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings")
async def test_refine_resume_stream_invalid_token(
    mock_get_user_settings,
    mock_decrypt_data,
    mock_async_refine_experience,
    client_with_auth_and_resume,
    test_user,
):
    """Test SSE stream reports error on API key decryption failure."""
    mock_settings = UserSettings(user_id=test_user.id, encrypted_api_key="key")
    mock_get_user_settings.return_value = mock_settings

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert "Invalid API key. Please update your settings." in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]
    mock_async_refine_experience.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_auth_error(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
):
    """Test SSE stream reports error on LLM authentication failure within sse_generator."""
    mock_async_refine_experience.side_effect = AuthenticationError(
        message="auth error", response=Mock(), body=None
    )

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert "LLM authentication failed. Please check your API key." in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception,expected_message_part",
    [
        (ValueError("value error"), "Refinement failed: value error"),
        (Exception("generic error"), "An unexpected error occurred."),
    ],
)
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_errors_in_generator(
    mock_get_user_settings,
    mock_async_refine_experience,
    exception,
    expected_message_part,
    client_with_auth_and_resume,
):
    """
    Test that the SSE stream correctly handles exceptions raised from the
    orchestration function, which are caught inside the sse_generator.
    """
    mock_async_refine_experience.side_effect = exception

    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream?job_description=job"
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    events = text_content.strip().split("\n\n")
    assert len(events) == 2
    assert "event: error" in events[0]
    assert expected_message_part in events[0]
    assert "text-red-500" in events[0]
    assert "event: close" in events[1]


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.async_refine_experience_section")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_client_disconnect(
    mock_get_user_settings,
    mock_async_refine_experience,
    client_with_auth_and_resume,
    caplog,
):
    """Test that the SSE stream handles a ClientDisconnect gracefully."""
    from starlette.middleware.base import ClientDisconnect

    async def mock_generator_with_disconnect():
        raise ClientDisconnect()
        yield  # Make it a generator

    mock_async_refine_experience.return_value = mock_generator_with_disconnect()

    with caplog.at_level(logging.WARNING):
        with client_with_auth_and_resume.stream(
            "GET",
            "/api/resumes/1/refine/stream?job_description=job",
        ) as response:
            assert response.status_code == 200
            # The generator should yield the close event from the finally block
            # even when the client disconnects.
            content = response.read()
            assert b"event: close" in content

    assert "Client disconnected from SSE stream for resume 1." in caplog.text
    mock_async_refine_experience.assert_called_once()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai._create_refine_result_html")
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch("resume_editor.app.llm.orchestration.refine_role", new_callable=AsyncMock)
@patch(
    "resume_editor.app.llm.orchestration.analyze_job_description",
    new_callable=AsyncMock,
)
@patch("resume_editor.app.llm.orchestration.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.get_user_settings", return_value=None)
async def test_refine_resume_stream_integrated(
    mock_get_user_settings,
    mock_orch_extract_experience,
    mock_analyze_job,
    mock_refine_role,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certifications,
    mock_build_sections,
    mock_create_html,
    client_with_auth_and_resume,
    test_resume,
):
    """
    Test the full SSE stream generation with mocked LLM calls, including reconstruction.
    """
    from resume_editor.app.api.routes.route_models import ExperienceResponse
    from resume_editor.app.llm.models import JobAnalysis, RefinedRole
    from resume_editor.app.models.resume.experience import (
        Project,
        ProjectDescription,
        ProjectOverview,
        ProjectSkills,
        Role,
        RoleBasics,
        RoleSummary,
    )

    # Arrange
    # Use resume with two roles to test ordering
    test_resume.content = VALID_RESUME_TWO_ROLES

    # 1. Mock orchestrator dependencies
    mock_role_a = Role(
        basics=RoleBasics(company="A Company", title="A Role", start_date="2024-01-01")
    )
    mock_role_b = Role(
        basics=RoleBasics(company="B Company", title="B Role", start_date="2023-01-01")
    )
    mock_orch_extract_experience.return_value = ExperienceResponse(
        roles=[mock_role_a, mock_role_b], projects=[]
    )

    mock_job_analysis = JobAnalysis(
        key_skills=["a", "b"], primary_duties=["c"], themes=["d"]
    )
    mock_analyze_job.return_value = (
        mock_job_analysis,
        "Generated intro from orchestration",
    )

    mock_refined_role1 = RefinedRole(
        basics=RoleBasics(
            company="A Company", title="Refined A Role", start_date="2024-01-01"
        ),
        summary=RoleSummary(text="Refined Summary for A"),
    )
    mock_refined_role2 = RefinedRole(
        basics=RoleBasics(
            company="B Company", title="Refined B Role", start_date="2023-01-01"
        ),
        summary=RoleSummary(text="Refined Summary for B"),
    )

    # Mock the refinement to complete out of order
    async def refine_role_side_effect(*args, **kwargs):
        role_title = kwargs["role"].basics.title
        if role_title == "A Role":
            await _real_asyncio_sleep(0.02)  # Slower task
            return mock_refined_role1
        # B Role
        await _real_asyncio_sleep(0.01)  # Faster task
        return mock_refined_role2

    mock_refine_role.side_effect = refine_role_side_effect

    # 2. Mock reconstruction dependencies
    mock_extract_personal.return_value = MagicMock()
    mock_extract_education.return_value = MagicMock()
    # For experience, return a mock with projects to ensure they are preserved
    mock_project = Project(
        overview=ProjectOverview(title="Test Project"),
        description=ProjectDescription(text="A project description."),
        skills=ProjectSkills(skills=["testing"]),
    )
    mock_original_experience = ExperienceResponse(roles=[], projects=[mock_project])
    mock_extract_experience.return_value = mock_original_experience
    mock_extract_certifications.return_value = MagicMock()
    mock_build_sections.return_value = "reconstructed content"
    mock_create_html.return_value = "<html>final refined html</html>"

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        "/api/resumes/1/refine/stream?job_description=a%20new%20job&generate_introduction=true",
    ) as response:
        assert response.status_code == 200
        text_content = response.read().decode("utf-8")

    # Assert
    events = text_content.strip().split("\n\n")

    # Expected events: progress, progress, intro, 2x progress (refining), done, close
    assert len(events) == 7, f"Expected 7 events, but got {len(events)}: {events}"

    assert "event: progress" in events[0] and "Parsing resume" in events[0]
    assert "event: progress" in events[1] and "Analyzing job" in events[1]

    intro_event = next(e for e in events if "event: introduction_generated" in e)
    assert 'id="introduction-container"' in intro_event

    refining_events = [e for e in events if "Refining role" in e]
    assert len(refining_events) == 2
    assert any("Refining role &#x27;A Role @ A Company&#x27;..." in e for e in refining_events)
    assert any("Refining role &#x27;B Role @ B Company&#x27;..." in e for e in refining_events)

    done_event = next(e for e in events if "event: done" in e)
    assert "data: <html>final refined html</html>" in done_event

    close_event = next(e for e in events if "event: close" in e)
    assert close_event is not None

    # Assert mocks
    mock_analyze_job.assert_called_once()
    assert mock_refine_role.call_count == 2  # We have two roles in the fixture

    mock_extract_personal.assert_called_once()
    mock_build_sections.assert_called_once()

    # Check that the refined roles were re-ordered correctly before reconstruction
    reconstruct_kwargs = mock_build_sections.call_args.kwargs
    reconstructed_roles = reconstruct_kwargs["experience"].roles
    assert len(reconstructed_roles) == 2
    assert reconstructed_roles[0].basics.title == "Refined A Role"
    assert reconstructed_roles[1].basics.title == "Refined B Role"

    # Ensure original projects were preserved
    assert (
        reconstruct_kwargs["experience"].projects
        == mock_original_experience.projects
    )

    mock_create_html.assert_called_once_with(
        1,
        "experience",
        "reconstructed content",
        job_description="a new job",
        introduction="Generated intro from orchestration",
    )
