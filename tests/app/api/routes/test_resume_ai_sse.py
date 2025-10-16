from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
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
@patch(
    "resume_editor.app.api.routes.resume_ai.experience_refinement_sse_generator",
)
async def test_refine_resume_stream_route(
    mock_sse_generator, client_with_auth_and_resume, test_user, test_resume
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
    job_desc = "a job"
    gen_intro = False

    # Act
    with client_with_auth_and_resume.stream(
        "GET",
        f"/api/resumes/1/refine/stream?job_description={job_desc}&generate_introduction={gen_intro}",
    ) as response:
        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        content = response.read().decode("utf-8")
        assert "event: one" in content
        assert "event: two" in content

    mock_sse_generator.assert_called_once_with(
        db=ANY,
        user=test_user,
        resume=test_resume,
        job_description=job_desc,
        generate_introduction=gen_intro,
    )
