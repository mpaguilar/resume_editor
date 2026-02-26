"""Tests for resume_ai_logic_reconstruction module."""

from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction import (
    _reconstruct_refined_resume_content,
    process_refined_experience_result,
)


def test_reconstruct_refined_resume_content():
    """Test basic reconstruction of refined resume content."""
    original_content = """# Personal
## Banner
Original banner

# Education
BS Computer Science

# Experience
## Company A
### Role 1
Description
"""

    params = ProcessExperienceResultParams(
        resume_id=1,
        original_resume_content=original_content,
        resume_content_to_refine=original_content,
        refined_roles={},
        job_description="Test job",
        limit_refinement_years=None,
    )

    with patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction.extract_experience_info"
    ) as mock_extract:
        mock_experience = Mock()
        mock_experience.roles = []
        mock_experience.projects = []
        mock_extract.return_value = mock_experience

        with patch(
            "resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction.serialize_experience_to_markdown"
        ) as mock_serialize:
            mock_serialize.return_value = "# Experience\n"
            result = _reconstruct_refined_resume_content(params)
            assert "# Personal" in result
            assert "# Education" in result


@pytest.mark.asyncio
async def test_process_refined_experience_result():
    """Test async processing of refined experience result."""
    params = ProcessExperienceResultParams(
        resume_id=1,
        original_resume_content="# Resume",
        resume_content_to_refine="# Resume",
        refined_roles={},
        job_description="Test",
        limit_refinement_years=None,
    )

    with patch(
        "resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction._reconstruct_refined_resume_content"
    ) as mock_reconstruct:
        mock_reconstruct.return_value = "Refined content"
        result = await process_refined_experience_result(params)
        assert result == "Refined content"
