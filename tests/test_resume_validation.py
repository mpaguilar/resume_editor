from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.resume import (
    ResumeCreateRequest,
    ResumeUpdateRequest,
    create_resume,
    update_resume,
)


class TestResumeValidation:
    """Test cases for Markdown validation in resume creation and update."""

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True)
    @patch("resume_editor.app.api.routes.resume.parse_resume")
    @pytest.mark.asyncio
    async def test_create_resume_with_invalid_markdown_raises_422(
        self, mock_parse_resume,
    ):
        """Test that creating a resume with invalid Markdown raises a 422 error."""
        # Arrange
        request = ResumeCreateRequest(
            name="Test Resume", content="Invalid markdown content",
        )
        mock_parse_resume.side_effect = Exception("Parsing failed")

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await create_resume(request, mock_request, mock_db, mock_current_user)

        assert exc_info.value.status_code == 422
        assert "Invalid Markdown format" in exc_info.value.detail

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True)
    @patch("resume_editor.app.api.routes.resume.parse_resume")
    @patch("resume_editor.app.api.routes.resume.DatabaseResume")
    @pytest.mark.asyncio
    async def test_create_resume_with_valid_markdown_succeeds(
        self, mock_db_resume, mock_parse_resume,
    ):
        """Test that creating a resume with valid Markdown succeeds."""
        # Arrange
        request = ResumeCreateRequest(
            name="Test Resume", content="# Valid Markdown\n\nContent here",
        )
        mock_parse_resume.return_value = Mock()  # Successful parsing

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.name = "Test Resume"
        mock_db_resume.return_value = mock_resume
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1) or setattr(
            x, "name", "Test Resume",
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

        # Act
        response = await create_resume(
            request, mock_request, mock_db, mock_current_user,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"
        mock_parse_resume.assert_called_once_with("# Valid Markdown\n\nContent here")

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", False)
    @patch("resume_editor.app.api.routes.resume.DatabaseResume")
    @pytest.mark.asyncio
    async def test_create_resume_without_parser_skips_validation(self, mock_db_resume):
        """Test that creating a resume without parser available skips validation."""
        # Arrange
        request = ResumeCreateRequest(name="Test Resume", content="Any content")

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.name = "Test Resume"
        mock_db_resume.return_value = mock_resume
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1) or setattr(
            x, "name", "Test Resume",
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

        # Act
        response = await create_resume(
            request, mock_request, mock_db, mock_current_user,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True)
    @patch("resume_editor.app.api.routes.resume.parse_resume")
    @pytest.mark.asyncio
    async def test_update_resume_with_invalid_markdown_raises_422(
        self, mock_parse_resume,
    ):
        """Test that updating a resume with invalid Markdown raises a 422 error."""
        # Arrange
        resume_id = 1
        request = ResumeUpdateRequest(content="Invalid markdown content")
        mock_parse_resume.side_effect = Exception("Parsing failed")

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        mock_resume = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_resume(
                resume_id, request, mock_request, mock_db, mock_current_user,
            )

        assert exc_info.value.status_code == 422
        assert "Invalid Markdown format" in exc_info.value.detail

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", True)
    @patch("resume_editor.app.api.routes.resume.parse_resume")
    @pytest.mark.asyncio
    async def test_update_resume_with_valid_markdown_succeeds(self, mock_parse_resume):
        """Test that updating a resume with valid Markdown succeeds."""
        # Arrange
        resume_id = 1
        request = ResumeUpdateRequest(content="# Valid Markdown\n\nUpdated content")
        mock_parse_resume.return_value = Mock()  # Successful parsing

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.name = "Test Resume"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resume
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

        # Act
        response = await update_resume(
            resume_id, request, mock_request, mock_db, mock_current_user,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"
        mock_parse_resume.assert_called_once_with("# Valid Markdown\n\nUpdated content")

    @patch("resume_editor.app.api.routes.resume.PARSER_AVAILABLE", False)
    @pytest.mark.asyncio
    async def test_update_resume_without_parser_skips_validation(self):
        """Test that updating a resume without parser available skips validation."""
        # Arrange
        resume_id = 1
        request = ResumeUpdateRequest(content="Any content")

        mock_db = Mock()
        mock_request = Mock()
        mock_request.headers = {}
        mock_current_user = Mock()
        mock_current_user.id = 1

        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.name = "Test Resume"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_resume
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

        # Act
        response = await update_resume(
            resume_id, request, mock_request, mock_db, mock_current_user,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"
