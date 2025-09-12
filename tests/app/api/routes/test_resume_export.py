from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_resume_for_user
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
    "format_enum, render_function_path, settings_changes",
    [
        ("ats", "resume_editor.app.api.routes.resume_export.ats_render", {}),
        ("plain", "resume_editor.app.api.routes.resume_export.plain_render", {}),
        (
            "executive",
            "resume_editor.app.api.routes.resume_export.basic_render",
            {"executive_summary": True, "skills_matrix": True},
        ),
    ],
)
@patch("resume_editor.app.api.routes.resume_export.Document")
@patch("resume_editor.app.api.routes.resume_export.parse_resume_to_writer_object")
def test_export_resume_docx_formats_no_filter(
    mock_parse,
    mock_document_cls,
    client: TestClient,
    setup_resume_dependency,
    format_enum,
    render_function_path,
    settings_changes,
):
    """Test exporting a resume in various DOCX formats without filtering."""
    mock_parsed_resume = MagicMock()
    mock_parse.return_value = mock_parsed_resume
    mock_doc_instance = MagicMock()
    mock_doc_instance.save = MagicMock()
    mock_document_cls.return_value = mock_doc_instance

    with patch(render_function_path) as mock_render:
        response = client.get(f"/api/resumes/1/export/docx?format={format_enum}")

        assert response.status_code == 200
        mock_parse.assert_called_once_with(VALID_RESUME_CONTENT)
        mock_document_cls.assert_called_once()
        mock_render.assert_called_once()

        args, _ = mock_render.call_args
        rendered_settings = args[2]
        for key, value in settings_changes.items():
            assert getattr(rendered_settings, key) == value

        mock_doc_instance.save.assert_called_once()
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="Test Resume_{format_enum}.docx"'
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
@patch("resume_editor.app.api.routes.resume_export.ats_render")
@patch("resume_editor.app.api.routes.resume_export.Document")
@patch("resume_editor.app.api.routes.resume_export.parse_resume_to_writer_object")
def test_export_resume_docx_with_filter(
    mock_parse,
    mock_document_cls,
    mock_render,
    mock_extract_personal,
    mock_extract_education,
    mock_extract_experience,
    mock_extract_certs,
    mock_filter_experience,
    mock_build_sections,
    client: TestClient,
    setup_resume_dependency,
):
    """Test exporting a resume in DOCX format with date filtering."""
    mock_doc_instance = MagicMock()
    mock_doc_instance.save = MagicMock()
    mock_document_cls.return_value = mock_doc_instance

    response = client.get(
        "/api/resumes/1/export/docx?format=ats&start_date=2021-01-01"
    )
    assert response.status_code == 200
    mock_build_sections.assert_called_once()
    mock_parse.assert_called_once_with(FILTERED_RESUME_CONTENT)
    mock_render.assert_called_once()


@patch(
    "resume_editor.app.api.routes.resume_export.parse_resume_to_writer_object",
    side_effect=TypeError("parsing failed"),
)
def test_export_resume_docx_parsing_error(
    mock_parse, client: TestClient, setup_resume_dependency
):
    """Test error handling during DOCX export when parsing fails."""
    response = client.get("/api/resumes/1/export/docx?format=ats")
    assert response.status_code == 422
    assert "Failed to generate docx" in response.json()["detail"]


@patch(
    "resume_editor.app.api.routes.resume_export.build_complete_resume_from_sections",
    side_effect=TypeError("filtering failed"),
)
@patch("resume_editor.app.api.routes.resume_export.extract_personal_info")
def test_export_resume_docx_filtering_error(
    mock_extract_personal,
    mock_build_sections,
    client: TestClient,
    setup_resume_dependency,
):
    """Test error handling during DOCX export when filtering fails."""
    response = client.get(
        "/api/resumes/1/export/docx?format=ats&start_date=2021-01-01"
    )
    assert response.status_code == 422
    assert "Failed to generate docx" in response.json()["detail"]


@patch("resume_editor.app.api.routes.resume_export.parse_resume_to_writer_object")
def test_export_resume_docx_invalid_format_safeguard(
    mock_parse, client: TestClient, setup_resume_dependency
):
    """Test safeguard for an invalid docx format that bypasses FastAPI validation."""
    mock_parsed_resume = MagicMock()
    mock_parse.return_value = mock_parsed_resume

    # This test is to hit the safeguard `case _:` which is not normally reachable.
    # We patch DocxFormat inside the route module to be a different class,
    # causing the `match` statement to fail.
    class FakeDocxFormat:
        ATS = "not-ats"
        PLAIN = "not-plain"
        EXECUTIVE = "not-executive"

    with patch(
        "resume_editor.app.api.routes.resume_export.DocxFormat", FakeDocxFormat
    ):
        response = client.get("/api/resumes/1/export/docx?format=ats")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid format specified"
