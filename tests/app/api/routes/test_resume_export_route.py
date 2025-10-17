import io
from copy import deepcopy
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.database.database import get_db
from resume_editor.app.api.routes.route_models import RenderFormat, RenderSettingsName
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)

# Sample resume content for testing
VALID_RESUME_CONTENT = """
# Personal
## Contact Information
Name: John Doe

# Experience
## Roles
### Role
#### Basics
Company: TestCo
Title: Engineer
Start date: 01/2020
End date: 12/2022
"""

FILTERED_RESUME_CONTENT = "filtered content"


@pytest.fixture
def app():
    """Create a new app instance for each test."""
    _app = create_app()
    yield _app


@pytest.fixture
def client(app):
    """Create a new client for each test."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db():
    """Fixture for a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def setup_db_dependency(app: "FastAPI", mock_db: MagicMock):
    """Fixture to set up database dependency override."""

    def get_mock_db():
        yield mock_db

    app.dependency_overrides[get_db] = get_mock_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_resume():
    """Fixture for a mock resume object."""
    resume_data = ResumeData(
        user_id=1, name="Test Resume", content=VALID_RESUME_CONTENT
    )
    _mock_resume = DatabaseResume(data=resume_data)
    _mock_resume.id = 1
    return _mock_resume


@pytest.fixture
def setup_resume_dependency(app, mock_resume):
    """Fixture to set up database resume dependency override."""

    def override_get_resume_for_user():
        return mock_resume

    app.dependency_overrides[get_resume_for_user] = override_get_resume_for_user
    yield
    app.dependency_overrides.clear()


def test_export_resume_markdown_no_filter(client: TestClient, setup_resume_dependency):
    """Test exporting a resume in Markdown format without any filtering."""
    response = client.get("/api/resumes/1/export/markdown")
    assert response.status_code == 200
    assert response.text == VALID_RESUME_CONTENT
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert (
        response.headers["content-disposition"] == 'attachment; filename="Test Resume.md"'
    )


@pytest.mark.parametrize(
    "url, expected_start, expected_end",
    [
        (
            "/api/resumes/1/export/markdown?start_date=2021-01-01",
            date(2021, 1, 1),
            None,
        ),
        (
            "/api/resumes/1/export/markdown?end_date=2022-12-31",
            None,
            date(2022, 12, 31),
        ),
        (
            "/api/resumes/1/export/markdown?start_date=2021-01-01&end_date=2022-12-31",
            date(2021, 1, 1),
            date(2022, 12, 31),
        ),
    ],
)
@patch(
    "resume_editor.app.api.routes.resume_export.build_complete_resume_from_sections",
    return_value=FILTERED_RESUME_CONTENT,
)
@patch("resume_editor.app.api.routes.resume_export.filter_experience_by_date")
@patch("resume_editor.app.api.routes.resume_export.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_export.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_export.extract_education_info")
@patch("resume_editor.app.api.routes.resume_export.extract_personal_info")
def test_export_resume_markdown_with_filter(
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certs,
    mock_filter_experience,
    mock_build_sections,
    client: TestClient,
    setup_resume_dependency,
    url: str,
    expected_start: date | None,
    expected_end: date | None,
):
    """Test exporting a resume in Markdown format with date filtering."""
    mock_personal = MagicMock()
    mock_education = MagicMock()
    mock_experience = MagicMock()
    mock_certs = MagicMock()
    mock_filtered_experience = MagicMock()

    mock_extract_personal.return_value = mock_personal
    mock_extract_education.return_value = mock_education
    mock_extract_experience.return_value = mock_experience
    mock_extract_certs.return_value = mock_certs
    mock_filter_experience.return_value = mock_filtered_experience

    response = client.get(url)

    assert response.status_code == 200

    mock_extract_personal.assert_called_once_with(VALID_RESUME_CONTENT)
    mock_extract_education.assert_called_once_with(VALID_RESUME_CONTENT)
    mock_extract_experience.assert_called_once_with(VALID_RESUME_CONTENT)
    mock_extract_certs.assert_called_once_with(VALID_RESUME_CONTENT)

    mock_filter_experience.assert_called_once_with(
        mock_experience, expected_start, expected_end
    )
    mock_build_sections.assert_called_once_with(
        personal_info=mock_personal,
        education=mock_education,
        experience=mock_filtered_experience,
        certifications=mock_certs,
    )
    assert response.text == FILTERED_RESUME_CONTENT


@patch(
    "resume_editor.app.api.routes.resume_export._get_filtered_resume_content",
    side_effect=ValueError("parsing failed"),
)
def test_export_resume_markdown_parsing_error(
    mock_get_filtered_content, client: TestClient, setup_resume_dependency
):
    """Test error handling during markdown export when parsing fails."""
    response = client.get("/api/resumes/1/export/markdown?start_date=2021-01-01")
    assert response.status_code == 422
    assert "Failed to filter resume" in response.json()["detail"]


def test_export_resume_markdown_invalid_date_format(
    client: TestClient, setup_resume_dependency
):
    """Test that an invalid date format returns a 400 error for markdown export."""
    response = client.get("/api/resumes/1/export/markdown?start_date=invalid-date")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date format. Please use YYYY-MM-DD."


@patch("resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream")
def test_download_resume_unauthenticated(
    mock_render_stream: MagicMock, client: TestClient, setup_db_dependency
):
    """Test that unauthenticated access to download is forbidden."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 401
    mock_render_stream.assert_not_called()


def test_export_markdown_unauthenticated(
    client: TestClient, setup_db_dependency
):
    """Test that unauthenticated access to markdown export is forbidden."""
    response = client.get(
        "/api/resumes/1/export/markdown",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 401




@pytest.mark.parametrize(
    "render_format, settings_name",
    [
        (RenderFormat.ATS, RenderSettingsName.GENERAL),
        (RenderFormat.PLAIN, RenderSettingsName.GENERAL),
        (RenderFormat.PLAIN, RenderSettingsName.EXECUTIVE_SUMMARY),
    ],
)
@patch("resume_editor.app.api.routes.resume_export.get_render_settings")
@patch("resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream")
def test_download_resume(
    mock_render_stream,
    mock_get_settings,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
    render_format,
    settings_name,
):
    """Test downloading a resume saves default export settings."""
    mock_settings_dict = {
        "section": {"experience": {}},
        "some_setting": "some_value",
    }
    mock_get_settings.return_value = mock_settings_dict
    mock_render_stream.return_value = io.BytesIO(b"test download docx")

    response = client.get(
        f"/api/resumes/1/download?render_format={render_format.value}&settings_name={settings_name.value}"
    )

    assert response.status_code == 200
    assert response.content == b"test download docx"

    # Assert settings were saved with defaults (False for checkboxes)
    assert mock_resume.export_settings_include_projects is False
    assert mock_resume.export_settings_render_projects_first is False
    assert mock_resume.export_settings_include_education is False
    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()

    mock_get_settings.assert_called_once_with(settings_name.value)
    # Check that original settings dict is not mutated
    assert mock_settings_dict == {
        "section": {"experience": {}},
        "some_setting": "some_value",
    }

    # settings_form has defaults of False, which are saved to the resume object
    expected_settings_dict = deepcopy(mock_settings_dict)
    expected_settings_dict["education"] = False
    expected_settings_dict["section"]["experience"]["projects"] = False
    expected_settings_dict["section"]["experience"]["render_projects_first"] = False

    mock_render_stream.assert_called_once_with(
        resume_content=VALID_RESUME_CONTENT,
        render_format=render_format.value,
        settings_dict=expected_settings_dict,
    )

    expected_filename = (
        f"Test_Resume-{render_format.value}-{settings_name.value}.docx"
    )
    assert (
        response.headers["content-disposition"]
        == f"attachment; filename={expected_filename}"
    )




@patch("resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream")
@patch(
    "resume_editor.app.api.routes.resume_export._get_filtered_resume_content",
    return_value=FILTERED_RESUME_CONTENT,
)
@patch("resume_editor.app.api.routes.resume_export.get_render_settings")
def test_download_resume_with_filter(
    mock_get_settings,
    mock_get_filtered_content,
    mock_render_stream,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
):
    """Test downloading a resume with date filtering."""
    mock_render_stream.return_value = io.BytesIO(b"filtered docx")
    mock_settings_dict = {
        "section": {"experience": {}},
        "some_setting": "some_value",
    }
    mock_get_settings.return_value = mock_settings_dict

    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general&start_date=2021-01-01"
    )

    assert response.status_code == 200
    assert response.content == b"filtered docx"

    mock_get_filtered_content.assert_called_once_with(
        VALID_RESUME_CONTENT, date(2021, 1, 1), None
    )

    mock_get_settings.assert_called_once_with(RenderSettingsName.GENERAL.value)

    # The settings from the form (defaulting to False) are persisted and then used to override.
    expected_settings_dict = deepcopy(mock_settings_dict)
    expected_settings_dict["education"] = False
    expected_settings_dict["section"]["experience"]["projects"] = False
    expected_settings_dict["section"]["experience"]["render_projects_first"] = False

    mock_render_stream.assert_called_once_with(
        resume_content=FILTERED_RESUME_CONTENT,
        render_format=RenderFormat.ATS.value,
        settings_dict=expected_settings_dict,
    )

    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()


@patch(
    "resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream",
    side_effect=ValueError("parsing failed"),
)
def test_download_resume_rendering_value_error(
    mock_render,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
):
    """Test error handling during download when rendering raises ValueError."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general"
    )
    assert response.status_code == 400
    assert "parsing failed" in response.json()["detail"]
    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()


@patch(
    "resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream",
    side_effect=Exception("some other error"),
)
def test_download_resume_rendering_other_error(
    mock_render,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
):
    """Test error handling during download when rendering raises any other exception."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general"
    )
    assert response.status_code == 500
    assert "Failed to generate docx during rendering" in response.json()["detail"]
    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()


@patch(
    "resume_editor.app.api.routes.resume_export._get_filtered_resume_content",
    side_effect=ValueError("filtering failed"),
)
def test_download_resume_filtering_error(
    mock_get_filtered_content,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
):
    """Test error handling during download when filtering/parsing raises an error."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general&start_date=2021-01-01"
    )
    assert response.status_code == 422
    assert "Failed to generate docx" in response.json()["detail"]
    # DB calls happen before filtering
    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()


def test_download_resume_invalid_date_format(
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
):
    """Test that an invalid date format returns a 400 error."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general&start_date=invalid-date"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date format. Please use YYYY-MM-DD."

    # The exception is raised after db commit
    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()


@pytest.mark.parametrize(
    "form_data, expected_projects, expected_render_first, expected_education",
    [
        (
            {"include_projects": "true"},
            True,
            False,
            False,
        ),
        (
            {"render_projects_first": "true"},
            False,
            True,
            False,
        ),
        (
            {"include_education": "true"},
            False,
            False,
            True,
        ),
        (
            {
                "include_projects": "true",
                "render_projects_first": "true",
                "include_education": "true",
            },
            True,
            True,
            True,
        ),
        (
            {},  # Empty form data, defaults should be False
            False,
            False,
            False,
        ),
    ],
)
@patch("resume_editor.app.api.routes.resume_export.get_render_settings")
@patch("resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream")
def test_download_resume_saves_settings(
    mock_render_stream,
    mock_get_settings: MagicMock,
    client: TestClient,
    mock_resume: DatabaseResume,
    mock_db: MagicMock,
    setup_resume_dependency,
    setup_db_dependency,
    form_data: dict,
    expected_projects: bool,
    expected_render_first: bool,
    expected_education: bool,
):
    """Test that download_resume saves the export settings from the form."""
    base_settings = {
        "section": {"experience": {}},
        "some_setting": "some_value",
    }
    mock_get_settings.return_value = base_settings
    mock_render_stream.return_value = io.BytesIO(b"test docx")

    # The form fields are boolean, but are sent as strings by html forms.
    # FastAPI handles this conversion.
    query_params = {
        "render_format": "ats",
        "settings_name": "general",
    }
    all_params = query_params.copy()
    all_params.update(form_data)
    response = client.get(
        "/api/resumes/1/download",
        params=all_params,
    )

    assert response.status_code == 200
    assert mock_resume.export_settings_include_projects is expected_projects
    assert mock_resume.export_settings_render_projects_first is expected_render_first
    assert mock_resume.export_settings_include_education is expected_education

    mock_db.add.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()

    assert base_settings == {
        "section": {"experience": {}},
        "some_setting": "some_value",
    }

    expected_settings = deepcopy(base_settings)
    expected_settings["education"] = expected_education
    expected_settings["section"]["experience"]["projects"] = expected_projects
    expected_settings["section"]["experience"][
        "render_projects_first"
    ] = expected_render_first

    mock_render_stream.assert_called_once_with(
        resume_content=VALID_RESUME_CONTENT,
        render_format="ats",
        settings_dict=expected_settings,
    )


def test_download_resume_invalid_params(
    client: TestClient, setup_resume_dependency
):
    """Test downloading with invalid query parameters."""
    # Invalid render_format
    response = client.get(
        "/api/resumes/1/download?render_format=invalid&settings_name=general"
    )
    assert response.status_code == 422
    assert "Input should be 'plain' or 'ats'" in response.text

    # Invalid settings_name
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=invalid"
    )
    assert response.status_code == 422
    assert "Input should be 'general' or 'executive_summary'" in response.text
