from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)
from resume_editor.app.models.user import User, UserData


@pytest.mark.asyncio
async def test_get_resume_for_user_success():
    """Test that get_resume_for_user returns a resume when it exists and belongs to the user."""
    mock_db = Mock()
    mock_user = User(
        data=UserData(username="test", email="test@test.com", hashed_password="pw", id_=1)
    )
    resume_data = ResumeData(user_id=1, name="Test", content="...")
    mock_resume = DatabaseResume(data=resume_data)
    mock_resume.id = 123

    # Mock the return value of get_resume_by_id_and_user
    with patch(
        "resume_editor.app.api.dependencies.get_resume_by_id_and_user"
    ) as mock_get:
        mock_get.return_value = mock_resume

        # Call the dependency function
        result = await get_resume_for_user(resume_id=123, db=mock_db, current_user=mock_user)

        # Assertions
        assert result == mock_resume
        mock_get.assert_called_once_with(mock_db, resume_id=123, user_id=1)


@pytest.mark.asyncio
async def test_get_resume_for_user_not_found():
    """Test that get_resume_for_user raises HTTPException when resume not found."""
    mock_db = Mock()
    mock_user = User(
        data=UserData(username="test", email="test@test.com", hashed_password="pw", id_=1)
    )

    # Mock the side effect of get_resume_by_id_and_user
    with patch(
        "resume_editor.app.api.dependencies.get_resume_by_id_and_user"
    ) as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="Resume not found")

        # Call the dependency function and assert it raises an exception
        with pytest.raises(HTTPException) as exc_info:
            await get_resume_for_user(resume_id=999, db=mock_db, current_user=mock_user)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resume not found"
        mock_get.assert_called_once_with(mock_db, resume_id=999, user_id=1)
