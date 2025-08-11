from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

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
    # Mock the resume_writer imports
    with (
        patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True),
        patch("resume_editor.app.api.routes.resume.parse_resume") as mock_parse,
    ):
        # Create a mock Resume object
        mock_resume = MagicMock()
        mock_resume.model_dump.return_value = {
            "personal": {
                "contact_info": {"name": "John Doe", "email": "john.doe@example.com"},
            },
        }
        mock_parse.return_value = mock_resume

        response = client.post(
            "/api/resumes/parse", json={"markdown_content": SAMPLE_MARKDOWN},
        )

        assert response.status_code == 200
        data = response.json()
        assert "resume_data" in data
        assert data["resume_data"]["personal"]["contact_info"]["name"] == "John Doe"


def test_parse_resume_parser_not_available(client):
    """Test parsing when parser is not available."""
    with patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", False):
        response = client.post(
            "/api/resumes/parse", json={"markdown_content": SAMPLE_MARKDOWN},
        )

        assert response.status_code == 501
        assert "not available" in response.json()["detail"]


def test_parse_resume_parsing_error(client):
    """Test parsing when an error occurs."""
    # Mock the resume_writer imports
    with (
        patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True),
        patch("resume_editor.app.api.routes.resume.parse_resume") as mock_parse,
    ):
        mock_parse.side_effect = Exception("Parsing error")

        response = client.post(
            "/api/resumes/parse", json={"markdown_content": SAMPLE_MARKDOWN},
        )

        assert response.status_code == 400
        assert "Failed to parse" in response.json()["detail"]
