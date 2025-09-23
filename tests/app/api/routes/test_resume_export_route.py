import io
from datetime import date
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.api.routes.route_models import RenderFormat, RenderSettingsName
from resume_editor.app.main import create_app
from resume_editor.app.models.resume_model import Resume as DatabaseResume

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
def setup_resume_dependency(app):
    """Fixture to set up database resume dependency override."""
    mock_resume = DatabaseResume(
        user_id=1, name="Test Resume", content=VALID_RESUME_CONTENT
    )
    mock_resume.id = 1

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

    response = client.get("/api/resumes/1/export/markdown?start_date=2021-01-01")

    assert response.status_code == 200
    mock_extract_personal.assert_called_with(VALID_RESUME_CONTENT)
    mock_extract_education.assert_called_with(VALID_RESUME_CONTENT)
    mock_extract_experience.assert_called_with(VALID_RESUME_CONTENT)
    mock_extract_certs.assert_called_with(VALID_RESUME_CONTENT)
    mock_filter_experience.assert_called_with(
        mock_experience, date(2021, 1, 1), None
    )
    mock_build_sections.assert_called_with(
        personal_info=mock_personal,
        education=mock_education,
        experience=mock_filtered_experience,
        certifications=mock_certs,
    )
    assert response.text == FILTERED_RESUME_CONTENT


@patch(
    "resume_editor.app.api.routes.resume_export.extract_personal_info",
    side_effect=ValueError("parsing failed"),
)
def test_export_resume_markdown_parsing_error(
    mock_extract_personal, client: TestClient, setup_resume_dependency
):
    """Test error handling during markdown export when parsing fails."""
    response = client.get("/api/resumes/1/export/markdown?start_date=2021-01-01")
    assert response.status_code == 422
    assert "Failed to filter resume" in response.json()["detail"]




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
@patch("resume_editor.app.api.routes.resume_export.extract_personal_info")
def test_download_rendered_resume(
    mock_extract_personal,
    mock_render_stream,
    mock_get_settings,
    client: TestClient,
    setup_resume_dependency,
    render_format,
    settings_name,
):
    """Test downloading a rendered resume without filtering."""
    mock_settings_dict = {"some_setting": "some_value"}
    mock_get_settings.return_value = mock_settings_dict
    mock_render_stream.return_value = io.BytesIO(b"test download docx")

    response = client.get(
        f"/api/resumes/1/download?render_format={render_format.value}&settings_name={settings_name.value}"
    )

    assert response.status_code == 200
    assert response.content == b"test download docx"

    # Ensure filtering logic was NOT called
    mock_extract_personal.assert_not_called()

    mock_get_settings.assert_called_once_with(settings_name.value)
    mock_render_stream.assert_called_once_with(
        resume_content=VALID_RESUME_CONTENT,
        render_format=render_format.value,
        settings_dict=mock_settings_dict,
    )

    expected_filename = (
        f"Test_Resume-{render_format.value}-{settings_name.value}.docx"
    )
    assert (
        response.headers["content-disposition"]
        == f"attachment; filename={expected_filename}"
    )


def test_download_rendered_resume_unauthenticated(client: TestClient):
    """Test that unauthenticated access to download is forbidden."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 401


@patch(
    "resume_editor.app.api.routes.resume_export.build_complete_resume_from_sections",
    return_value=FILTERED_RESUME_CONTENT,
)
@patch("resume_editor.app.api.routes.resume_export.filter_experience_by_date")
@patch("resume_editor.app.api.routes.resume_export.extract_certifications_info")
@patch("resume_editor.app.api.routes.resume_export.extract_experience_info")
@patch("resume_editor.app.api.routes.resume_export.extract_education_info")
@patch("resume_editor.app.api.routes.resume_export.extract_personal_info")
@patch("resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream")
def test_download_rendered_resume_with_filter(
    mock_render_stream,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certs,
    mock_filter_experience,
    mock_build_sections,
    client: TestClient,
    setup_resume_dependency,
):
    """Test downloading a rendered resume with date filtering."""
    mock_render_stream.return_value = io.BytesIO(b"filtered docx")
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

    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general&start_date=2021-01-01"
    )

    assert response.status_code == 200
    assert response.content == b"filtered docx"
    mock_build_sections.assert_called_once_with(
        personal_info=mock_personal,
        education=mock_education,
        experience=mock_filtered_experience,
        certifications=mock_certs,
    )
    mock_render_stream.assert_called_once()
    assert mock_render_stream.call_args.kwargs["resume_content"] == FILTERED_RESUME_CONTENT


@patch(
    "resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream",
    side_effect=ValueError("parsing failed"),
)
def test_download_rendered_resume_rendering_value_error(
    mock_render, client: TestClient, setup_resume_dependency
):
    """Test error handling during download when rendering raises ValueError."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general"
    )
    assert response.status_code == 400
    assert "parsing failed" in response.json()["detail"]


@patch(
    "resume_editor.app.api.routes.resume_export.render_resume_to_docx_stream",
    side_effect=Exception("some other error"),
)
def test_download_rendered_resume_rendering_other_error(
    mock_render, client: TestClient, setup_resume_dependency
):
    """Test error handling during download when rendering raises any other exception."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general"
    )
    assert response.status_code == 500
    assert "Failed to generate docx during rendering" in response.json()["detail"]


@patch(
    "resume_editor.app.api.routes.resume_export.extract_personal_info",
    side_effect=ValueError("filtering failed"),
)
def test_download_rendered_resume_filtering_error(
    mock_extract_personal,
    client: TestClient,
    setup_resume_dependency,
):
    """Test error handling during download when filtering/parsing raises an error."""
    response = client.get(
        "/api/resumes/1/download?render_format=ats&settings_name=general&start_date=2021-01-01"
    )
    assert response.status_code == 422
    assert "Failed to generate docx" in response.json()["detail"]


def test_download_rendered_resume_invalid_params(
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
