from unittest.mock import ANY, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_db, get_resume_for_user
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
    ProjectsResponse,
)
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


@pytest.fixture
def client_with_auth_no_resume(app):
    def get_resume_for_user_not_found():
        raise HTTPException(status_code=404, detail="Resume not found")

    app.dependency_overrides[get_resume_for_user] = get_resume_for_user_not_found
    return TestClient(app)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/resumes/999/personal",
        "/api/resumes/999/education",
        "/api/resumes/999/experience",
        "/api/resumes/999/projects",
        "/api/resumes/999/certifications",
    ],
)
def test_get_info_not_found(client_with_auth_no_resume: TestClient, endpoint: str):
    """Test GET endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.get(endpoint)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


@pytest.mark.parametrize(
    "endpoint, payload",
    [
        ("/api/resumes/999/personal", {"name": "test"}),
        (
            "/api/resumes/999/education",
            {"degrees": [{"school": "test", "degree": "BSc"}]},
        ),
        (
            "/api/resumes/999/experience",
            {
                "roles": [
                    {
                        "basics": {
                            "company": "test",
                            "title": "t",
                            "start_date": "2023-01-01T00:00:00",
                        },
                    },
                ],
            },
        ),
        (
            "/api/resumes/999/projects",
            {
                "projects": [
                    {
                        "overview": {
                            "title": "A Project",
                            "start_date": "2023-01-01T00:00:00",
                            "url": None,
                            "url_description": None,
                            "end_date": None,
                        },
                        "description": {"text": "A description of the project."},
                        "skills": {"skills": ["Python"]},
                    },
                ],
            },
        ),
        ("/api/resumes/999/certifications", {"certifications": [{"name": "test"}]}),
    ],
)
def test_update_info_not_found(
    client_with_auth_no_resume: TestClient, endpoint: str, payload: dict
):
    """Test PUT endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.put(endpoint, json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


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
    response_data = response.json()
    assert response_data["name"] == "new name"
    assert response_data["email"] == "new@email.com"

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


def test_get_education_info_success(
    client_with_auth_and_resume: TestClient, test_resume: DatabaseResume
):
    """Test successful retrieval of education info."""
    with patch(
        "resume_editor.app.api.routes.resume_edit.extract_education_info"
    ) as mock_extract:
        mock_extract.return_value = EducationResponse(degrees=[])
        response = client_with_auth_and_resume.get(
            f"/api/resumes/{test_resume.id}/education"
        )
        assert response.status_code == 200
        assert response.json() == {"degrees": []}
        mock_extract.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_education_info_structured_success(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of education info."""
    mock_update_content.return_value = "new updated content"
    payload = {"degrees": [{"school": "new school", "degree": "BSc"}]}

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/education",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["degrees"][0]["school"] == "new school"

    mock_update_content.assert_called_once()
    call_kwargs = mock_update_content.call_args.kwargs
    assert call_kwargs["current_content"] == test_resume.content
    assert isinstance(call_kwargs["education"], EducationResponse)
    assert call_kwargs["education"].degrees[0].school == "new school"

    mock_validate.assert_called_once_with(
        "new updated content",
        test_resume.content,
    )

    mock_update_db.assert_called_once()
    assert mock_update_db.call_args.args[1] == test_resume
    assert mock_update_db.call_args.kwargs["content"] == "new updated content"


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_education_info_reconstruction_error(
    mock_update_content,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume: DatabaseResume,
):
    """Test that a reconstruction error during education update is handled."""
    mock_update_content.side_effect = ValueError("Parsing failed")
    payload = {"degrees": [{"school": "new school", "degree": "BSc"}]}

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/education",
        json=payload,
    )

    assert response.status_code == 422
    assert "Parsing failed" in response.json()["detail"]
    mock_update_db.assert_not_called()


# Tests for update_education form
from resume_editor.app.api.routes.html_fragments import _generate_resume_detail_html


@patch("resume_editor.app.api.routes.resume_edit.extract_education_info")
@patch(
    "resume_editor.app.api.routes.resume_edit._generate_resume_detail_html",
    return_value="<html>Updated</html>",
)
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_db",
)
@patch(
    "resume_editor.app.api.routes.resume_edit.perform_pre_save_validation",
)
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data",
)
def test_update_education_success_form(
    mock_reconstruct,
    mock_validate,
    mock_update_db,
    mock_gen_html,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful form update of education info."""
    from datetime import datetime

    mock_extract.return_value = EducationResponse(degrees=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "school": "New School",
        "degree": "BSc",
        "start_date": "2020-01-01",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/education",
        data=form_data,
    )

    assert response.status_code == 200
    mock_extract.assert_called_once_with(test_resume.content)

    mock_reconstruct.assert_called_once()
    _, kwargs = mock_reconstruct.call_args
    assert kwargs["current_content"] == test_resume.content
    education_arg = kwargs["education"]
    assert len(education_arg.degrees) == 1
    assert education_arg.degrees[0].school == "New School"
    assert education_arg.degrees[0].start_date == datetime(2020, 1, 1)


def test_update_education_invalid_data_form(
    client_with_auth_and_resume: TestClient, test_resume
):
    """Test invalid data for education form update."""
    form_data = {"school": "New School", "start_date": "invalid-date"}
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/education",
        data=form_data,
    )
    assert response.status_code == 422
    assert "Failed to update education info" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_edit.extract_education_info")
def test_update_education_extraction_fails_form(
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a parsing failure during education form update is handled."""
    mock_extract.side_effect = ValueError("Bad education section")
    form_data = {
        "school": "New School",
        "degree": "BSc",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/education",
        data=form_data,
    )
    assert response.status_code == 422
    assert (
        "Failed to update education info: Bad education section"
        in response.json()["detail"]
    )


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
    response_data = response.json()
    assert response_data["projects"][0]["overview"]["title"] == "new title"
    assert response_data["projects"][0]["description"]["text"] == "A new project."

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
@patch("resume_editor.app.api.routes.resume_edit.extract_experience_info")
def test_update_projects_info_structured_validation_error(
    mock_extract,
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a validation error during structured update of projects is handled."""
    mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
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


def test_get_certifications_info_success(
    client_with_auth_and_resume: TestClient, test_resume: DatabaseResume
):
    """Test successful retrieval of certifications info."""
    with patch(
        "resume_editor.app.api.routes.resume_edit.extract_certifications_info",
    ) as mock_extract:
        mock_extract.return_value = CertificationsResponse(certifications=[])
        response = client_with_auth_and_resume.get(
            f"/api/resumes/{test_resume.id}/certifications"
        )
        assert response.status_code == 200
        assert response.json() == {"certifications": []}
        mock_extract.assert_called_once_with(test_resume.content)


@patch("resume_editor.app.api.routes.resume_edit.update_resume_db")
@patch("resume_editor.app.api.routes.resume_edit.perform_pre_save_validation")
@patch(
    "resume_editor.app.api.routes.resume_edit.update_resume_content_with_structured_data"
)
def test_update_certifications_info_structured_success(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of certifications info."""
    mock_update_content.return_value = "new updated content"
    payload = {"certifications": [{"name": "new cert"}]}

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/certifications",
        json=payload,
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["certifications"][0]["name"] == "new cert"

    mock_update_content.assert_called_once()
    call_kwargs = mock_update_content.call_args.kwargs
    assert call_kwargs["current_content"] == test_resume.content
    assert isinstance(call_kwargs["certifications"], CertificationsResponse)
    assert call_kwargs["certifications"].certifications[0].name == "new cert"

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
def test_update_certifications_info_structured_validation_error(
    mock_update_content,
    mock_validate,
    mock_update_db,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a validation error during structured update of certifications is handled."""
    mock_update_content.return_value = "new updated content"
    mock_validate.side_effect = HTTPException(
        status_code=422,
        detail="Validation failed",
    )
    payload = {"certifications": [{"name": "new cert"}]}

    response = client_with_auth_and_resume.put(
        f"/api/resumes/{test_resume.id}/certifications",
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
    patch(
        "resume_editor.app.api.routes.resume_edit._generate_resume_detail_html",
        return_value="<html>Updated</html>",
    ),
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
    mock_gen_html,
    mock_update_db,
    mock_validate,
    mock_reconstruct,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of projects info."""
    mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "title": "New Project",
        "description": "A cool project",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/projects",
        data=form_data,
    )

    assert response.status_code == 200
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


# Tests for update_certifications
@patch("resume_editor.app.api.routes.resume_edit.extract_certifications_info")
@apply_form_update_patches
def test_update_certifications_success(
    mock_gen_html,
    mock_update_db,
    mock_validate,
    mock_reconstruct,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful update of certifications info."""
    mock_extract.return_value = CertificationsResponse(certifications=[])
    mock_update_db.return_value = test_resume

    form_data = {
        "name": "New Cert",
        "issuer": "Test Issuer",
        "issued_date": "2023-03-01",
        "id": "CERT-12345",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/certifications",
        data=form_data,
    )

    assert response.status_code == 200
    mock_extract.assert_called_once_with(test_resume.content)

    mock_reconstruct.assert_called_once()
    _, kwargs = mock_reconstruct.call_args
    certifications_arg = kwargs["certifications"]
    assert len(certifications_arg.certifications) == 1
    assert certifications_arg.certifications[0].name == "New Cert"
    assert certifications_arg.certifications[0].certification_id == "CERT-12345"


def test_update_certifications_invalid_data(
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test invalid data for certifications update."""
    form_data = {"name": "New Cert", "issued_date": "invalid"}
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/certifications",
        data=form_data,
    )
    assert response.status_code == 422
    assert "Failed to update certifications info" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_edit.extract_certifications_info")
def test_update_certifications_extraction_fails(
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test that a parsing failure during certifications update is handled."""
    mock_extract.side_effect = ValueError("Bad certifications section")
    form_data = {
        "name": "New Cert",
    }
    response = client_with_auth_and_resume.post(
        f"/api/resumes/{test_resume.id}/edit/certifications",
        data=form_data,
    )
    assert response.status_code == 422
    assert (
        "Failed to update certifications info: Bad certifications section"
        in response.json()["detail"]
    )


def test_get_experience_info_success(
    client_with_auth_and_resume: TestClient, test_resume: DatabaseResume
):
    """Test successful retrieval of experience info."""
    from resume_editor.app.api.routes.route_models import ExperienceResponse

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
    response_data = response.json()
    assert response_data["roles"][0]["basics"]["company"] == "new co"

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
    assert mock_update_db.call_args.kwargs["content"] == "new updated content"


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
    "resume_editor.app.api.routes.resume_edit._generate_resume_detail_html",
    return_value="<html>Updated</html>",
)
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
    mock_gen_html,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test successful form update of experience info."""
    from resume_editor.app.api.routes.route_models import ExperienceResponse

    mock_extract.return_value = ExperienceResponse(roles=[], projects=[])
    mock_update_db.return_value = test_resume

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
    """Test invalid data for experience form update."""
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
    """Test that a parsing failure during experience form update is handled."""
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
