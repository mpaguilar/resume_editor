from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.routes.resume import (
    ResumeCreateRequest,
    ResumeUpdateRequest,
    create_resume,
    update_resume,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    perform_pre_save_validation,
)


class TestResumeValidation:
    """Test cases for Markdown validation in resume creation and update."""

    def test_perform_pre_save_validation_success(self):
        """Test that pre-save validation passes with valid content."""
        # Arrange
        content = """# Personal

## Contact Information

Name: John Doe

# Education

## Degrees

### Degree

School: University of Example

# Experience

## Roles

### Role

#### Basics
Company: Tech Corp
Title: Software Engineer"""

        # Act & Assert
        with patch(
            "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content",
        ) as mock_validate:
            mock_validate.return_value = None  # Success
            # Should not raise an exception
            perform_pre_save_validation(content)
            mock_validate.assert_called_once_with(content)

    def test_perform_pre_save_validation_failure(self):
        """Test that pre-save validation raises HTTPException with invalid content."""
        # Arrange
        content = "Invalid content without proper sections"

        # Act & Assert
        with patch(
            "resume_editor.app.api.routes.route_logic.resume_validation.validate_resume_content",
        ) as mock_validate:
            mock_validate.side_effect = HTTPException(
                status_code=422,
                detail="Invalid Markdown format",
            )
            with pytest.raises(HTTPException) as exc_info:
                perform_pre_save_validation(content)

        assert exc_info.value.status_code == 422
        assert "Invalid Markdown format" in exc_info.value.detail
        mock_validate.assert_called_once_with(content)

    @patch("resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume")
    @pytest.mark.asyncio
    async def test_create_resume_with_invalid_markdown_raises_422(
        self,
        mock_parse_resume,
    ):
        """Test that creating a resume with invalid Markdown raises a 422 error."""
        # Arrange
        request = ResumeCreateRequest(
            name="Test Resume",
            content="Invalid markdown content",
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

    @patch("resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume")
    @patch("resume_editor.app.api.routes.resume.DatabaseResume")
    @pytest.mark.asyncio
    async def test_create_resume_with_valid_markdown_succeeds(
        self,
        mock_db_resume,
        mock_parse_resume,
    ):
        """Test that creating a resume with valid Markdown succeeds."""
        # Arrange
        request = ResumeCreateRequest(
            name="Test Resume",
            content="# Valid Markdown\n\nContent here",
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
            x,
            "name",
            "Test Resume",
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_resume]

        # Act
        response = await create_resume(
            request,
            mock_request,
            mock_db,
            mock_current_user,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"
        mock_parse_resume.assert_called_once_with("# Valid Markdown\n\nContent here")

    @patch("resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume")
    @pytest.mark.asyncio
    async def test_update_resume_with_invalid_markdown_raises_422(
        self,
        mock_parse_resume,
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
                resume_id,
                request,
                mock_request,
                mock_db,
                mock_current_user,
                mock_resume,
            )

        assert exc_info.value.status_code == 422
        assert "Invalid Markdown format" in exc_info.value.detail

    @patch("resume_editor.app.api.routes.route_logic.resume_parsing.parse_resume")
    @pytest.mark.asyncio
    async def test_update_resume_with_valid_markdown_succeeds(self, mock_parse_resume):
        """Test that updating a resume with valid Markdown succeeds."""
        # Arrange
        content = """# Personal

## Contact Information

Name: John Doe
Email: john@example.com

# Education

## Degrees

### Degree

School: University of Example

# Experience

## Roles

### Role

#### Basics
Company: Tech Corp
Title: Software Engineer"""

        resume_id = 1
        request = ResumeUpdateRequest(content=content)
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
            resume_id,
            request,
            mock_request,
            mock_db,
            mock_current_user,
            mock_resume,
        )

        # Assert
        assert response.id == 1
        assert response.name == "Test Resume"
        mock_parse_resume.assert_called_once_with(content)
