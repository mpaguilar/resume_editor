from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_db, get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_crud import ResumeUpdateParams
from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)


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
    resume_data = ResumeData(
        user_id=1,
        name="Test Resume",
        content=valid_minimal_resume_content,
        is_active=True,
    )
    resume = DatabaseResume(data=resume_data)
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


def test_get_experience_info_success(
    client_with_auth_and_resume: TestClient, test_resume: DatabaseResume
):
    """Test successful retrieval of experience info."""

    with patch(
        "resume_editor.app.api.routes.resume_edit.extract_experience_info",
    ) as mock_extract:
        mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
        response = client_with_auth_and_resume.get(
            f"/api/resumes/{test_resume.id}/experience"
        )
        assert response.status_code == 200
        assert response.json() == {"roles": [], "projects": []}
        mock_extract.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_experience_info_structured_success(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of experience info."""
    from resume_editor.app.api.routes.route_models import ExperienceResponse

    mock_update_content.return_value = "new updated content"
    payload = {
        "roles": [
            {
                "basics": {
                    "company": "new co",
                    "title": "new title",
                    "start_date": "2023-01-01T00:00:00",
                },
            },
        ],
        "projects": [],
    }

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/experience",
        json=payload,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_update_content.assert_called_once()
    call_kwargs = mock_update_content.call_args.kwargs
    assert call_kwargs["current_content"] == test_resume.content
    assert isinstance(call_kwargs["experience"], ExperienceResponse)
    assert call_kwargs["experience"].roles[0].basics.company == "new co"

    mock_validate.assert_called_once_with(
        "new updated content",
        test_resume.content,
    )

    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.args[1] == test_resume
    params = mock_update_db.call_args.kwargs["params"]
    assert isinstance(params, ResumeUpdateParams)
    assert params.content == "new updated content"


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_experience_info_reconstruction_error(
    mock_update_content,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume: DatabaseResume,
):
    """Test that a reconstruction error during experience update is handled."""
    mock_update_content.side_effect = ValueError("Parsing failed")
    payload = {
        "roles": [
            {
                "basics": {
                    "company": "new co",
                    "title": "new title",
                    "start_date": "2023-01-01T00:00:00",
                },
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/experience",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_db.assert_not_called()


@patch("resume_editor.app.api.routes.resume_edit.extract_experience_info")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_db",
)
@patch(
    "resume_editor.app.api.routes.resume_edit.perform_pre_save_validation",
)
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data",
)
def test_update_experience_success_form(
    mock_reconstruct,
    mock_validate,
    mock_update_db,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test adding a new experience role via form submission."""
    from resume_editor.app.api.routes.route_models import ExperienceResponse

    mock_reconstruct.return_value = "Updated Content"
    mock_extract.return_value = ExperienceResponse(roles=[], projects=[])

    form_data = {
        "company": "New Company",
        "title": "Developer",
        "start_date": "2021-02-01",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/experience",
        data=form_data,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract.assert_called_once_with(test_resume.content)

    mock_reconstruct.assert_called_once()
    _, kwargs = mock_reconstruct.call_args
    experience_arg = kwargs["experience"]
    assert len(experience_arg.roles) == 1
    assert experience_arg.roles[0].basics.company == "New Company"


def test_update_experience_invalid_data_form(
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that invalid form data for experience role creation is handled."""
    form_data = {"company": "New Co", "title": "Dev", "start_date": "invalid"}
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/experience",
        data=form_data,
    )
    assert response.status_code == 422
    assert "Failed to update experience info" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_edit.extract_experience_info")
def test_update_experience_extraction_fails_form(
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a parsing failure during experience role creation via form is handled."""
    from resume_editor.app.api.routes.route_models import ExperienceResponse

    mock_extract.side_effect = ValueError("Bad experience section")
    form_data = {
        "company": "New Company",
        "title": "Developer",
        "start_date": "2024-01-01",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/experience",
        data=form_data,
    )
    assert response.status_code == 422
    assert (
        "Failed to update experience info: Bad experience section"
        in response.json()["detail"]
    )
