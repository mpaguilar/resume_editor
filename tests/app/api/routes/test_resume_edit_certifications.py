from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_db, get_resume_for_user
from resume_editor.app.api.routes.route_logic.resume_crud import ResumeUpdateParams
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
)
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
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content

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
    params = mock_update_db.call_args.kwargs["params"]
    assert isinstance(params, ResumeUpdateParams)
    assert params.content == "new updated content"


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
]


def apply_form_update_patches(func):
    """A decorator to apply a list of patches to a test function."""
    for p in reversed(form_update_patches):
        func = p(func)
    return func


# Tests for update_certifications
@patch("resume_editor.app.api.routes.resume_edit.extract_certifications_info")
@apply_form_update_patches
def test_update_certifications_success(
    mock_update_db,
    mock_validate,
    mock_reconstruct,
    mock_extract,
    client_with_auth_and_resume: TestClient,
    test_resume,
):
    """Test adding a new certification via form submission."""
    mock_extract.return_value = CertificationsResponse(certifications=[])

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
    assert response.headers["HX-Redirect"] == "/dashboard"
    assert not response.content
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
    """Test that invalid form data for certification creation is handled."""
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
    """Test that a parsing failure during certification creation via form is handled."""
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
