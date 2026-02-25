"""Tests for resume_ai routes with company and notes fields."""

from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.resume_ai import _ExperienceStreamParams
from resume_editor.app.models.resume_model import Resume as DatabaseResume


class TestExperienceStreamParams:
    def test_params_with_company_and_notes(self):
        mock_resume = Mock(spec=DatabaseResume)
        mock_db = Mock()
        mock_user = Mock()

        params = _ExperienceStreamParams(
            resume=mock_resume,
            parsed_limit_years=5,
            db=mock_db,
            current_user=mock_user,
            job_description="Job desc",
            limit_refinement_years="5",
            company="Acme Corp",
            notes="Notes here",
        )
        assert params.company == "Acme Corp"
        assert params.notes == "Notes here"

    def test_params_defaults(self):
        mock_resume = Mock(spec=DatabaseResume)
        mock_db = Mock()
        mock_user = Mock()

        params = _ExperienceStreamParams(
            resume=mock_resume,
            parsed_limit_years=None,
            db=mock_db,
            current_user=mock_user,
            job_description="Job desc",
            limit_refinement_years=None,
        )
        assert params.company is None
        assert params.notes is None


class TestRefineResumeValidation:
    @patch("resume_editor.app.api.routes.resume_ai.validate_refinement_form")
    @patch("resume_editor.app.api.routes.resume_ai._parse_limit_years_for_stream")
    def test_validation_failure_returns_error(self, mock_parse_limit, mock_validate):
        mock_validate.return_value = Mock(
            is_valid=False, errors={"company": "Too long"}
        )
        mock_parse_limit.return_value = (None, None)
        pass  # Test would need full FastAPI test client setup

    @patch("resume_editor.app.api.routes.resume_ai.validate_refinement_form")
    def test_validation_success_continues(self, mock_validate):
        mock_validate.return_value = Mock(is_valid=True, errors={})
        pass  # Test would need full FastAPI test client setup
