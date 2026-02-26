"""Tests for resume_ai_logic_helpers module."""

import logging
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers import (
    get_llm_config,
    handle_save_as_new_refinement,
    process_refined_experience_result,
)
from resume_editor.app.api.routes.route_models import SaveAsNewParams
from resume_editor.app.models.resume_model import Resume as DatabaseResume

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestGetLlmConfig:
    """Tests for get_llm_config function."""

    def test_get_llm_config_returns_tuple_with_all_values(self):
        """Test that get_llm_config returns tuple with endpoint, model, and api_key."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_settings = Mock()
        mock_settings.llm_endpoint = "https://api.example.com"
        mock_settings.llm_model_name = "gpt-4"
        mock_settings.encrypted_api_key = b"encrypted_key"

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.get_user_settings",
            return_value=mock_settings,
        ):
            with patch(
                "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.decrypt_data",
                return_value="decrypted_api_key",
            ):
                # Act
                result = get_llm_config(mock_db, user_id=1)

                # Assert
                assert isinstance(result, tuple)
                assert len(result) == 3
                assert result[0] == "https://api.example.com"
                assert result[1] == "gpt-4"
                assert result[2] == "decrypted_api_key"

    def test_get_llm_config_handles_none_settings(self):
        """Test that get_llm_config handles None settings gracefully."""
        # Arrange
        mock_db = Mock(spec=Session)

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.get_user_settings",
            return_value=None,
        ):
            # Act
            result = get_llm_config(mock_db, user_id=1)

            # Assert
            assert result == (None, None, None)

    def test_get_llm_config_handles_missing_api_key(self):
        """Test that get_llm_config handles missing API key."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_settings = Mock()
        mock_settings.llm_endpoint = "https://api.example.com"
        mock_settings.llm_model_name = "gpt-4"
        mock_settings.encrypted_api_key = None

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.get_user_settings",
            return_value=mock_settings,
        ):
            # Act
            result = get_llm_config(mock_db, user_id=1)

            # Assert
            assert result == ("https://api.example.com", "gpt-4", None)


class TestProcessRefinedExperienceResult:
    """Tests for process_refined_experience_result function."""

    def test_process_refined_experience_result_generates_html(self):
        """Test that process_refined_experience_result generates HTML content."""
        # Arrange
        mock_html = "<div>Refined Resume HTML</div>"

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers._create_refine_result_html",
            return_value=mock_html,
        ) as mock_create_html:
            # Act
            result = process_refined_experience_result(
                resume_id=1,
                final_content="# Resume Content",
                job_description="Job description text",
                introduction="Introduction text",
                limit_refinement_years=5,
                company="Test Company",
                notes="Some notes",
            )

            # Assert
            assert result == mock_html
            mock_create_html.assert_called_once()

    def test_process_refined_experience_result_handles_none_introduction(self):
        """Test that process_refined_experience_result handles None introduction."""
        # Arrange
        mock_html = "<div>Refined Resume HTML</div>"

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers._create_refine_result_html",
            return_value=mock_html,
        ) as mock_create_html:
            # Act
            result = process_refined_experience_result(
                resume_id=1,
                final_content="# Resume Content",
                job_description="Job description text",
                introduction=None,
                limit_refinement_years=None,
            )

            # Assert
            assert result == mock_html
            # Verify introduction was converted to empty string
            call_args = mock_create_html.call_args
            params = call_args.kwargs.get("params") or call_args.args[0]
            assert params.introduction == ""


class TestHandleSaveAsNewRefinement:
    """Tests for handle_save_as_new_refinement function."""

    def test_handle_save_as_new_refinement_creates_resume(self):
        """Test that handle_save_as_new_refinement creates a new resume."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.id = 1
        mock_resume = Mock(spec=DatabaseResume)
        mock_resume.id = 2

        mock_form_data = Mock()
        mock_form_data.refined_content = "# Refined Resume"
        mock_form_data.job_description = "Job description"
        mock_form_data.introduction = "New introduction"
        mock_form_data.new_resume_name = "My Refined Resume"
        mock_form_data.company = "Test Company"
        mock_form_data.notes = "Some notes"

        params = SaveAsNewParams(
            db=mock_db,
            user=mock_user,
            resume=mock_resume,
            form_data=mock_form_data,
        )

        mock_new_resume = Mock(spec=DatabaseResume)
        mock_new_resume.id = 3

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.perform_pre_save_validation",
        ):
            with patch(
                "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.validate_company_and_notes",
            ) as mock_validate:
                mock_validation_result = Mock()
                mock_validation_result.is_valid = True
                mock_validate.return_value = mock_validation_result

                with patch(
                    "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.create_resume_db",
                    return_value=mock_new_resume,
                ) as mock_create:
                    # Act
                    result = handle_save_as_new_refinement(params)

                    # Assert
                    assert result == mock_new_resume
                    mock_create.assert_called_once()

    def test_handle_save_as_new_refinement_raises_on_validation_failure(self):
        """Test that handle_save_as_new_refinement raises on validation failure."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.id = 1
        mock_resume = Mock(spec=DatabaseResume)
        mock_resume.id = 2

        mock_form_data = Mock()
        mock_form_data.refined_content = "# Refined Resume"
        mock_form_data.job_description = "Job description"
        mock_form_data.introduction = "New introduction"
        mock_form_data.new_resume_name = "My Refined Resume"
        mock_form_data.company = None
        mock_form_data.notes = None

        params = SaveAsNewParams(
            db=mock_db,
            user=mock_user,
            resume=mock_resume,
            form_data=mock_form_data,
        )

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.perform_pre_save_validation",
        ):
            with patch(
                "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.validate_company_and_notes",
            ) as mock_validate:
                mock_validation_result = Mock()
                mock_validation_result.is_valid = False
                mock_validation_result.errors = {"company": "Invalid company"}
                mock_validate.return_value = mock_validation_result

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    handle_save_as_new_refinement(params)

                assert exc_info.value.status_code == 400

    def test_handle_save_as_new_refinement_handles_mock_values(self):
        """Test that handle_save_as_new_refinement handles mock values for company/notes."""
        # Arrange
        mock_db = Mock(spec=Session)
        mock_user = Mock()
        mock_user.id = 1
        mock_resume = Mock(spec=DatabaseResume)
        mock_resume.id = 2

        # Mock that returns Mock for company/notes attributes
        mock_form_data = Mock()
        mock_form_data.refined_content = "# Refined Resume"
        mock_form_data.job_description = "Job description"
        mock_form_data.introduction = "New introduction"
        mock_form_data.new_resume_name = "My Refined Resume"

        params = SaveAsNewParams(
            db=mock_db,
            user=mock_user,
            resume=mock_resume,
            form_data=mock_form_data,
        )

        mock_new_resume = Mock(spec=DatabaseResume)
        mock_new_resume.id = 3

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.perform_pre_save_validation",
        ):
            with patch(
                "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.validate_company_and_notes",
            ) as mock_validate:
                mock_validation_result = Mock()
                mock_validation_result.is_valid = True
                mock_validate.return_value = mock_validation_result

                with patch(
                    "resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers.create_resume_db",
                    return_value=mock_new_resume,
                ) as mock_create:
                    # Act
                    result = handle_save_as_new_refinement(params)

                    # Assert
                    assert result == mock_new_resume
                    # Verify company and notes are None (not Mock)
                    call_args = mock_create.call_args
                    create_params = call_args.kwargs.get("params") or call_args.args[0]
                    assert create_params.company is None
                    assert create_params.notes is None
