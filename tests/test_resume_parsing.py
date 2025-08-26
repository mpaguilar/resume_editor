from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume,
    parse_resume_content,
    validate_resume_content,
)
from resume_editor.app.main import create_app, initialize_database

# Sample Markdown resume content for testing
SAMPLE_MARKDOWN = """
# John Doe

## Contact Information
* Name: John Doe
* Email: john.doe@example.com
* Phone: (555) 123-4567
* Location: San Francisco, CA

## Personal Summary
Experienced software engineer with 5 years of experience in Python and FastAPI development.
"""


@pytest.fixture
def client():
    with (
        patch("resume_editor.app.database.database.get_engine"),
        patch("resume_editor.app.models.Base.metadata.create_all"),
    ):
        app = create_app()
        initialize_database()
        return TestClient(app)


def test_parse_resume_success(client):
    """Test successful resume parsing."""
    with patch(
        "resume_editor.app.api.routes.resume.parse_resume_content",
    ) as mock_parse_content:
        # Mock the return value to match ParseResponse structure
        mock_parse_content.return_value = {
            "resume_data": {
                "personal": {
                    "contact_info": {
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                    },
                },
            },
        }

        response = client.post(
            "/api/resumes/parse",
            json={"markdown_content": SAMPLE_MARKDOWN},
        )

        assert response.status_code == 200
        data = response.json()
        assert "resume_data" in data
        assert data["resume_data"]["personal"]["contact_info"]["name"] == "John Doe"


def test_parse_resume_parsing_error(client):
    """Test parsing when an error occurs."""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_parsing.WriterResume.parse",
    ) as mock_parse:
        mock_parse.side_effect = Exception("Parsing error")

        response = client.post(
            "/api/resumes/parse",
            json={"markdown_content": SAMPLE_MARKDOWN},
        )

        assert response.status_code == 400
        assert "Failed to parse" in response.json()["detail"]


def test_parse_resume_no_model_dump():
    """Test parse_resume with an object that does not have model_dump."""

    class MockResume:
        def __init__(self):
            self.name = "John Doe"

    with patch(
        "resume_editor.app.api.routes.route_logic.resume_parsing.WriterResume.parse",
    ) as mock_parse:
        mock_parse.return_value = MockResume()
        result = parse_resume("markdown content")
        assert result == {"name": "John Doe"}


def test_parse_resume_content_success():
    """Test parse_resume_content successful execution."""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume",
        return_value={"some": "data"},
    ) as mock_parse_resume:
        result = parse_resume_content("some markdown")
        assert result == {"some": "data"}
        mock_parse_resume.assert_called_once_with("some markdown")


def test_validate_resume_content_failure():
    """Test validate_resume_content when parsing fails, raising an HTTPException."""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume",
        side_effect=Exception("Test validation failure"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            validate_resume_content("invalid markdown")

        assert exc_info.value.status_code == 422
        assert (
            "Invalid Markdown format: Test validation failure" == exc_info.value.detail
        )


def test_parse_resume_content_exception():
    """Test parse_resume_content handles exceptions from parse_resume."""
    with patch(
        "resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume",
        side_effect=Exception("mocked error"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            parse_resume_content("some invalid markdown")
        assert exc_info.value.status_code == 400
        assert "Failed to parse resume: mocked error" == exc_info.value.detail
