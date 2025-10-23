from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.api.routes.route_models import ExperienceRefinementParams
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData
from resume_editor.app.models.user import User as DBUser, UserData


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            id_=1,
        )
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content="some content",
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    return resume


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    _app = create_app()
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_with_auth_and_resume(app, client, test_user, test_resume):
    """Fixture for a test client with an authenticated user and a resume."""
    mock_db = Mock()
    query_mock = Mock()
    filter_mock = Mock()
    filter_mock.first.return_value = test_resume
    filter_mock.all.return_value = [test_resume]
    query_mock.filter.return_value = filter_mock
    mock_db.query.return_value = query_mock

    def get_mock_db_with_resume():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db_with_resume
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user
    return client


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_route(
    mock_sse_generator,
    mock_extract_exp,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """
    Test that the GET /refine/stream route correctly calls the SSE generator
    and streams its content.
    """
    # Arrange
    async def mock_generator():
        yield "event: one\ndata: 1\n\n"
        yield "event: two\ndata: 2\n\n"

    mock_sse_generator.return_value = mock_generator()
    mock_extract_exp.return_value = Mock(roles=[Mock()])  # Ensure roles are present
    job_desc = "a job"
    form_data = {
        "job_description": job_desc,
        "target_section": "experience",
    }

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream", params=form_data
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        content = response.read().decode("utf-8")
        assert "event: one" in content
        assert "event: two" in content

    mock_sse_generator.assert_called_once()
    # The generator is called with a keyword argument `params`.
    call_kwargs = mock_sse_generator.call_args.kwargs
    assert "params" in call_kwargs
    params_arg = call_kwargs["params"]
    assert isinstance(params_arg, ExperienceRefinementParams)
    assert params_arg.user == test_user
    assert params_arg.resume == test_resume
    assert params_arg.resume_content_to_refine == test_resume.content
    assert params_arg.job_description == job_desc
    mock_extract_exp.assert_called_once_with(test_resume.content)


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
@pytest.mark.parametrize(
    "limit_years_str, error_msg_part",
    [
        ("0", "must be a positive number"),
        ("-5", "must be a positive number"),
        ("abc", "must be a valid number"),
    ],
)
async def test_refine_resume_stream_invalid_limit(
    mock_sse_generator, client_with_auth_and_resume, limit_years_str, error_msg_part
):
    """
    Test that the stream refinement route returns an error for invalid limit_refinement_years.
    """
    # Arrange
    form_data = {
        "job_description": "a job",
        "target_section": "experience",
        "limit_refinement_years": limit_years_str,
    }

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream", params=form_data
    ) as response:
        # Assert
        assert response.status_code == 200
        content = response.read().decode("utf-8")
        assert "event: error" in content
        assert error_msg_part in content
        assert "event: close" in content

    mock_sse_generator.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.filter_experience_by_date")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_with_filtering(
    mock_sse_generator,
    mock_extract_personal,
    mock_extract_edu,
    mock_extract_exp,
    mock_extract_certs,
    mock_filter_exp,
    mock_build_resume,
    client_with_auth_and_resume,
    test_user,
    test_resume,
):
    """
    Test that the stream refinement route correctly filters experience by date
    when limit_refinement_years is provided.
    """
    # Arrange
    async def mock_generator():
        yield "data: done\n\n"

    mock_sse_generator.return_value = mock_generator()
    mock_build_resume.return_value = "filtered content"

    form_data = {
        "job_description": "a job",
        "target_section": "experience",
        "limit_refinement_years": "5",
    }

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream", params=form_data
    ) as response:
        # Assert
        assert response.status_code == 200
        response.read()

    mock_extract_personal.assert_called_once_with(test_resume.content)
    mock_extract_edu.assert_called_once_with(test_resume.content)
    # extract_experience_info is called in _build_filtered_content_if_needed,
    # and again in _experience_refinement_stream
    assert mock_extract_exp.call_count == 2
    mock_extract_certs.assert_called_once_with(test_resume.content)
    mock_filter_exp.assert_called_once()
    mock_build_resume.assert_called_once()

    mock_sse_generator.assert_called_once()
    # The generator is called with a keyword argument `params`.
    call_kwargs = mock_sse_generator.call_args.kwargs
    assert "params" in call_kwargs
    params_arg = call_kwargs["params"]
    assert isinstance(params_arg, ExperienceRefinementParams)
    assert params_arg.user == test_user
    assert params_arg.resume == test_resume
    assert params_arg.resume_content_to_refine == "filtered content"
    assert params_arg.job_description == "a job"


@pytest.mark.asyncio
@patch(
    "resume_editor.app.api.routes.resume_ai.extract_personal_info",
    side_effect=Exception("Kaboom!"),
)
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_with_filtering_exception(
    mock_sse_generator, mock_extract_personal, client_with_auth_and_resume
):
    """
    Test that the stream refinement route handles exceptions during experience filtering.
    """
    # Arrange
    form_data = {
        "job_description": "a job",
        "target_section": "experience",
        "limit_refinement_years": "5",
    }

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream", params=form_data
    ) as response:
        # Assert
        assert response.status_code == 200
        content = response.read().decode("utf-8")
        assert "event: error" in content
        assert "An error occurred while filtering experience." in content
        assert "event: close" in content

    mock_extract_personal.assert_called_once()
    mock_sse_generator.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.filter_experience_by_date")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_get_no_roles_after_filtering(
    mock_sse_generator,
    mock_extract_personal,
    mock_extract_edu,
    mock_extract_exp,
    mock_extract_certs,
    mock_filter_exp,
    mock_build_resume,
    client_with_auth_and_resume,
):
    """
    Test that the GET SSE stream sends a warning and closes if no roles are left after filtering.
    """
    # Arrange
    # This mock now applies to both calls to extract_experience_info
    mock_extract_exp.side_effect = [
        Mock(roles=[Mock()]),  # First call in _build_filtered_content_if_needed
        Mock(roles=[]),  # Second call in _experience_refinement_stream
    ]
    mock_build_resume.return_value = "filtered content with no roles"

    params = {
        "job_description": "a job",
        "limit_refinement_years": "5",
    }

    # Act
    with client_with_auth_and_resume.stream(
        "GET", "/api/resumes/1/refine/stream", params=params
    ) as response:
        # Assert
        assert response.status_code == 200
        content = response.read().decode("utf-8")
        assert "event: error" in content
        assert "No roles available to refine within the specified date range." in content
        assert "event: close" in content

    assert mock_extract_exp.call_count == 2
    mock_sse_generator.assert_not_called()


@pytest.mark.asyncio
@patch("resume_editor.app.api.routes.resume_ai.build_complete_resume_from_sections")
@patch("resume_editor.app.api.routes.resume_ai.filter_experience_by_date")
@patch("resume_editor.app.api.routes.resume_ai.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_education_info")
@patch("resume_editor.app.api.routes.resume_ai.extract_personal_info")
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_post_no_roles_after_filtering(
    mock_sse_generator,
    mock_extract_personal,
    mock_extract_edu,
    mock_extract_exp,
    mock_extract_certs,
    mock_filter_exp,
    mock_build_resume,
    client_with_auth_and_resume,
):
    """
    Test that the POST SSE stream sends a warning and closes if no roles are left after filtering.
    """
    # Arrange
    # First call inside _build_filtered_content_if_needed, second call in wrapper
    mock_extract_exp.side_effect = [
        Mock(roles=[Mock()]),  # has roles initially
        Mock(roles=[]),  # no roles after filtering/parsing
    ]
    mock_build_resume.return_value = "filtered content with no roles"

    form_data = {
        "job_description": "a job",
        "limit_refinement_years": "5",
        "target_section": "experience",
    }

    # Act
    with client_with_auth_and_resume.stream(
        "POST", "/api/resumes/1/refine/stream", data=form_data
    ) as response:
        # Assert
        assert response.status_code == 200
        content = response.read().decode("utf-8")
        assert "event: error" in content
        assert "No roles available to refine within the specified date range." in content
        assert "event: close" in content

    assert mock_extract_exp.call_count == 2
    mock_sse_generator.assert_not_called()


def test_refine_resume_experience_returns_sse_loader_with_hx_ext(
    client_with_auth_and_resume, test_resume
):
    """
    Test that POST /refine for 'experience' section returns the SSE loader
    HTML fragment with the correct `hx-ext="sse"` attribute.
    """
    # Arrange
    form_data = {
        "job_description": "A great job",
        "target_section": "experience",
    }

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine", data=form_data
    )

    # Assert
    assert response.status_code == 200
    html = response.text
    assert 'id="refine-sse-loader"' in html
    assert (
        f'sse-connect="/api/resumes/{test_resume.id}/refine/stream?job_description=A+great+job"'
        in html
    )
    assert 'hx-ext="sse"' in html
    assert 'sse-swap="done,error"' in html
    assert 'sse-close="close"' in html


def test_post_refine_stream_with_hx_request_returns_loader(
    client_with_auth_and_resume, test_resume
):
    """
    Test POST /refine/stream with HX-Request returns the SSE loader.
    """
    # Arrange
    form_data = {
        "job_description": "A job for POST",
        "target_section": "experience",
        "limit_refinement_years": "5",
    }
    headers = {"HX-Request": "true"}

    # Act
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/refine/stream",
        data=form_data,
        headers=headers,
    )

    # Assert
    assert response.status_code == 200
    html = response.text
    assert 'id="refine-sse-loader"' in html
    assert 'hx-ext="sse"' in html
    assert (
        f'sse-connect="/api/resumes/{test_resume.id}/refine/stream?job_description=A+job+for+POST&limit_refinement_years=5"'
        in html
    )
