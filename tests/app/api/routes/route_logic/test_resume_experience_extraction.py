from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
)
from resume_editor.app.models.resume.experience import InclusionStatus


@patch("resume_editor.app.api.routes.route_logic.resume_serialization._check_for_unparsed_content")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization._convert_writer_project_to_dict"
)
@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization._convert_writer_role_to_dict"
)
@patch("resume_editor.app.api.routes.route_logic.resume_serialization._parse_resume")
class TestRefactoredExtractExperienceInfo:
    """Unit tests for the refactored extract_experience_info function."""

    def test_happy_path(self, mock_parse, mock_role_conv, mock_proj_conv, mock_check):
        """Test happy path with roles and projects."""
        mock_parsed_resume = Mock()
        mock_experience = Mock()
        mock_role = Mock()
        mock_project = Mock()
        mock_experience.roles = [mock_role]
        mock_experience.projects = [mock_project]
        mock_parsed_resume.experience = mock_experience
        mock_parse.return_value = mock_parsed_resume

        mock_role_dict = {
            "basics": {
                "company": "Test Co",
                "title": "Dev",
                "start_date": datetime(2022, 1, 1),
            }
        }
        mock_proj_dict = {
            "overview": {"title": "Test Project", "inclusion_status": InclusionStatus.INCLUDE}
        }
        mock_role_conv.return_value = mock_role_dict
        mock_proj_conv.return_value = mock_proj_dict

        result = extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_called_once_with(mock_role)
        mock_proj_conv.assert_called_once_with(mock_project)
        mock_check.assert_not_called()

        assert len(result.roles) == 1
        assert len(result.projects) == 1
        assert result.roles[0].model_dump(exclude_unset=True) == mock_role_dict
        assert result.projects[0].model_dump(exclude_unset=True) == mock_proj_dict

    def test_empty_role_and_project_dicts_are_skipped(
        self, mock_parse, mock_role_conv, mock_proj_conv, mock_check
    ):
        """Test that empty dicts from helpers are skipped."""
        mock_parsed_resume = Mock()
        mock_experience = Mock()
        mock_role = Mock()
        mock_project = Mock()
        mock_experience.roles = [mock_role]
        mock_experience.projects = [mock_project]
        mock_parsed_resume.experience = mock_experience
        mock_parse.return_value = mock_parsed_resume

        mock_role_conv.return_value = {}
        mock_proj_conv.return_value = {}

        result = extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_called_once_with(mock_role)
        mock_proj_conv.assert_called_once_with(mock_project)
        mock_check.assert_called_once_with("some content", "experience", None)

        assert len(result.roles) == 0
        assert len(result.projects) == 0

    def test_no_experience_section(
        self, mock_parse, mock_role_conv, mock_proj_conv, mock_check
    ):
        """Test with no experience section in parsed resume."""
        mock_parsed_resume = Mock()
        mock_parsed_resume.experience = None
        mock_parse.return_value = mock_parsed_resume

        result = extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_not_called()
        mock_proj_conv.assert_not_called()
        mock_check.assert_called_once_with("some content", "experience", None)

        assert len(result.roles) == 0
        assert len(result.projects) == 0

    def test_experience_with_no_roles_or_projects(
        self, mock_parse, mock_role_conv, mock_proj_conv, mock_check
    ):
        """Test with experience section but no roles or projects lists."""
        mock_parsed_resume = Mock()
        mock_experience = Mock()
        mock_experience.roles = None
        mock_experience.projects = None
        mock_parsed_resume.experience = mock_experience
        mock_parse.return_value = mock_parsed_resume

        result = extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_not_called()
        mock_proj_conv.assert_not_called()
        mock_check.assert_called_once_with("some content", "experience", None)

        assert len(result.roles) == 0
        assert len(result.projects) == 0

    def test_experience_with_empty_roles_or_projects(
        self, mock_parse, mock_role_conv, mock_proj_conv, mock_check
    ):
        """Test with experience section with empty roles or projects lists."""
        mock_parsed_resume = Mock()
        mock_experience = Mock()
        mock_experience.roles = []
        mock_experience.projects = []
        mock_parsed_resume.experience = mock_experience
        mock_parse.return_value = mock_parsed_resume

        result = extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_not_called()
        mock_proj_conv.assert_not_called()
        mock_check.assert_called_once_with("some content", "experience", None)

        assert len(result.roles) == 0
        assert len(result.projects) == 0

    def test_parse_fails_raises_error(
        self, mock_parse, mock_role_conv, mock_proj_conv, mock_check
    ):
        """Test that a ValueError from parsing is re-raised."""
        mock_parse.side_effect = ValueError("parse fail")

        with pytest.raises(
            ValueError, match="Failed to parse experience info from resume content."
        ):
            extract_experience_info("some content")

        mock_parse.assert_called_once_with("some content")
        mock_role_conv.assert_not_called()
        mock_proj_conv.assert_not_called()
        mock_check.assert_not_called()
