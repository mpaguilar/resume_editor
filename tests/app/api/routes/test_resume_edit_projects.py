from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_db, get_resume_for_user
from resume_editor.app.api.routes.route_models import ExperienceResponse
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


def test_get_projects_info_success(
    client_with_auth_and_resume: TestClient, test_resume: DatabaseResume
):
    """Test successful retrieval of projects info."""
    with patch(
        "resume_editor.app.api.routes.resume_edit.extract_experience_info",
    ) as mock_extract:
        mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
        response = client_with_auth_and_resume.get(
            f"/api/resumes/{test_resume.id}/projects"
        )
        assert response.status_code == 200
        assert response.json() == {"projects": []}
        mock_extract.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_projects_info_structured_success(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of projects info."""
    mock_update_content.return_value = "new updated content"
    payload = {
        "projects": [
            {
                "overview": {
                    "title": "new title",
                    "start_date": "2024-01-01T00:00:00",
                    "url": None,
                    "url_description": None,
                    "end_date": None,
                },
                "description": {"text": "A new project."},
                "skills": {"skills": ["Skill 1"]},
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/projects",
        json=payload,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

    mock_update_content.assert_called_once()
    call_kwargs = mock_update_content.call_args.kwargs
    assert call_kwargs["current_content"] == test_resume.content
    assert isinstance(call_kwargs["experience"], ExperienceResponse)
    assert call_kwargs["experience"].projects[0].overview.title == "new title"
    assert len(call_kwargs["experience"].roles) == 1

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
def test_update_projects_info_structured_validation_error(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a validation error during structured update of projects is handled."""
    mock_update_content.return_value = "new updated content"
    mock_validate.side_effect = HTTPException(
        status_code=422,
        detail="Validation failed",
    )
    payload = {
        "projects": [
            {
                "overview": {"title": "new title"},
                "description": {"text": "A new project."},
            },
        ],
    }

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/projects",
        json=payload,
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


# --- Form update tests ---

# Common patch decorators for form-based update tests
form_update_patches = [
    patch(
        "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data",
        return_value="Updated Content",
    ),
    patch(
        "resume_editor.app.api.routes.resume_edit.perform_pre_save_validation",
        return_value=None,
    ),
    patch("resume_editor.app.api.routes.resume_edit.update_resume_db"),
]


def apply_form_update_patches(func):
    """A decorator to apply a list of patches to a test function."""
    for p in reversed(form_update_patches):
        func = p(func)
    return func


# Tests for update_projects
@patch("resume_editor.app.api.routes.resume_edit.extract_experience_info")
@apply_form_update_patches
def test_update_projects_success(
    mock_update_db,
    mock_validate,
    mock_reconstruct,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of projects info."""
    mock_extract.return_value = ExperienceResponse(roles=[], projects=[])

    form_data = {
        "title": "New Project",
        "description": "A cool project",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/projects",
        data=form_data,
    )

    assert response.status_code == 200
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
    mock_extract.assert_called_once_with(test_resume.content)

    mock_reconstruct.assert_called_once()
    _, kwargs = mock_reconstruct.call_args
    experience_arg = kwargs["experience"]
    assert len(experience_arg.projects) == 1
    assert experience_arg.projects[0].overview.title == "New Project"


def test_update_projects_invalid_data(
    client_with_auth_and_resume: TestClient, test_resume
):
    """Test invalid data for projects update."""
    form_data = {
        "title": "New Project",
        "description": "A cool project",
        "start_date": "invalid",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/projects",
        data=form_data,
    )
    assert response.status_code == 422
    assert "Failed to update projects info" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_edit.extract_experience_info")
def test_update_projects_extraction_fails(
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a parsing failure during projects update is handled."""
    mock_extract.side_effect = ValueError("Bad projects section")
    form_data = {
        "title": "New Project",
        "description": "A cool project",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/projects",
        data=form_data,
    )
    assert response.status_code == 422
    assert (
        "Failed to update projects info: Bad projects section"
        in response.json()["detail"]
    )
