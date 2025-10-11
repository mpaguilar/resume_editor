from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_db, get_resume_for_user
from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume


@pytest.fixture
def valid_minimal_resume_content() -> str:
    """A valid resume in Markdown format."""
    return """# Personal
## Contact Information

Name: Jane Doe
# Education
## Degrees
### Degree

School: State University
# Certifications
## Certification

Name: Certified Professional
# Experience
## Roles
### Role
#### Basics

Company: A Company, LLC

Title: Engineer

Start date: 01/2020
## Projects
### Project
#### Overview

Title: A Project
#### Description

A description of the project.
"""


@pytest.fixture
def test_resume(valid_minimal_resume_content: str) -> DatabaseResume:
    """A test resume object."""
    resume = DatabaseResume(
        user_id=1,
        name="Test Resume",
        content=valid_minimal_resume_content,
        is_active=True,
    )
    resume.id = 1
    return resume


@pytest.fixture
def app():
    """A FastAPI app instance."""
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_auth_and_resume(app, test_resume):
    def get_resume_for_user_found():
        return test_resume

    def get_mock_db():
        yield None  # db not used if endpoints are mocked properly

    app.dependency_overrides[get_resume_for_user] = get_resume_for_user_found
    app.dependency_overrides[get_db] = get_mock_db
    return TestClient(app)


def test_get_personal_info_success(
    client_with_auth_and_resume: TestClient,
    test_resume: DatabaseResume,
):
    """Test successful retrieval of personal info."""
    with patch(
        "resume_editor.app.api.routes.resume_edit.extract_personal_info"
    ) as mock_extract:
        mock_extract.return_value = PersonalInfoResponse(name="Test User")
        response = client_with_auth_and_resume.get(
            f"/api/resumes/{test_resume.id}/personal"
        )
        assert response.status_code == 200
        assert response.json() == {
            "name": "Test User",
            "email": None,
            "phone": None,
            "location": None,
            "website": None,
            "github": None,
            "linkedin": None,
            "twitter": None,
            "work_authorization": None,
            "require_sponsorship": None,
            "banner": None,
            "note": None,
        }
        mock_extract.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_personal_info_structured_success(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of personal info."""
    mock_update_content.return_value = "new updated content"
    payload = {"name": "new name", "email": "new@email.com"}

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/personal",
        json=payload,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_update_content.assert_called_once()
    call_kwargs = mock_update_content.call_args.kwargs
    assert call_kwargs["current_content"] == test_resume.content
    assert isinstance(call_kwargs["personal_info"], PersonalInfoResponse)
    assert call_kwargs["personal_info"].name == "new name"
    assert "education" not in call_kwargs
    assert "experience" not in call_kwargs
    assert "certifications" not in call_kwargs

    mock_validate.assert_called_once_with(
        "new updated content",
        test_resume.content,
    )

    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.args[1] == test_resume
    assert mock_update_db.call_args.kwargs["content"] == "new updated content"


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_personal_info_structured_validation_error(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a validation error during structured update is handled."""
    mock_update_content.return_value = "new updated content"
    mock_validate.side_effect = HTTPException(
        status_code=422,
        detail="Validation failed",
    )

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/personal",
        json={"name": "new name"},
    )

    assert response.status_code == 422
    expected_detail = (
        "Failed to update resume due to reconstruction/validation error: Validation failed"
    )
    assert response.json()["detail"] == expected_detail
    mock_update_content.assert_called_once()
    mock_validate.assert_called_once_with(
        "new updated content",
        test_resume.content,
    )
    mock_update_db.assert_not_called()
