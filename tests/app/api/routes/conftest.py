import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.core.config import get_settings
from resume_editor.app.core.security import get_password_hash
from resume_editor.app.database.database import get_db
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume, ResumeData
from resume_editor.app.models.user import User as DBUser, UserData


VALID_MINIMAL_RESUME_CONTENT = """# Personal

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
"""


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            attributes={},
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
        content=VALID_MINIMAL_RESUME_CONTENT,
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    return resume


@pytest.fixture
def app():
    """Fixture to create a new app for each test."""
    get_settings.cache_clear()
    _app = create_app()
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Fixture to create a test client for each test."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def client_with_db(app):
    """Fixture for a test client with a mocked database."""
    mock_db = Mock()

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    with TestClient(app) as c:
        yield c, mock_db


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
