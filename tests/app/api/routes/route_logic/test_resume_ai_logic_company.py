"""Tests for resume_ai_logic with company and notes fields."""

from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic import (
    handle_save_as_new_refinement,
)
from resume_editor.app.api.routes.route_models import SaveAsNewParams


class MockSaveAsNewForm:
    """Mock form data for testing."""

    def __init__(
        self,
        refined_content: str,
        new_resume_name: str | None = None,
        company: str | None = None,
        notes: str | None = None,
        job_description: str | None = None,
        introduction: str | None = None,
    ):
        self.refined_content = refined_content
        self.new_resume_name = new_resume_name
        self.company = company
        self.notes = notes
        self.job_description = job_description
        self.introduction = introduction
        self.limit_refinement_years = None


class TestHandleSaveAsNewRefinement:
    @patch("resume_editor.app.api.routes.route_logic.resume_ai_logic.create_resume_db")
    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
    )
    def test_saves_company_and_notes(self, mock_validate, mock_create_resume):
        mock_validate.return_value = Mock(is_valid=True, errors={})
        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_resume = Mock()
        mock_resume.id = 5

        mock_new_resume = Mock()
        mock_create_resume.return_value = mock_new_resume

        form_data = MockSaveAsNewForm(
            refined_content="Refined content",
            new_resume_name="New Resume",
            company="Acme Corp",
            notes="Notes here",
            job_description="Job desc",
            introduction="Intro",
        )

        params = SaveAsNewParams(
            db=mock_db, user=mock_user, resume=mock_resume, form_data=form_data
        )

        result = handle_save_as_new_refinement(params)

        assert result == mock_new_resume
        mock_create_resume.assert_called_once()
        create_params = mock_create_resume.call_args[1]["params"]
        assert create_params.company == "Acme Corp"
        assert create_params.notes == "Notes here"

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic.perform_pre_save_validation"
    )
    def test_validation_failure_raises_exception(self, mock_validate):
        from fastapi import HTTPException

        mock_validate.return_value = Mock(
            is_valid=False, errors={"company": "Too long"}
        )

        mock_db = Mock()
        mock_user = Mock()
        mock_resume = Mock()

        form_data = MockSaveAsNewForm(
            refined_content="Refined content",
            new_resume_name="New Resume",
            company="A" * 300,  # Too long
        )

        params = SaveAsNewParams(
            db=mock_db, user=mock_user, resume=mock_resume, form_data=form_data
        )

        with pytest.raises(HTTPException) as exc_info:
            handle_save_as_new_refinement(params)

        assert exc_info.value.status_code == 400
