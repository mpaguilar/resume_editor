import logging
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.resume_crud import (
    create_resume,
    delete_resume,
    get_resume_by_id_and_user,
    get_user_resumes,
    update_resume,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)


def test_get_resume_by_id_and_user_found():
    """Test get_resume_by_id_and_user when resume is found."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_resume

    result = get_resume_by_id_and_user(db=mock_db, resume_id=1, user_id=1)

    assert result == mock_resume
    mock_db.query.assert_called_once_with(DatabaseResume)
    assert mock_db.query.return_value.filter.call_count == 1
    mock_db.query.return_value.filter.return_value.first.assert_called_once()


def test_get_resume_by_id_and_user_not_found():
    """Test get_resume_by_id_and_user when resume is not found."""
    mock_db = Mock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_resume_by_id_and_user(db=mock_db, resume_id=1, user_id=1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Resume not found"


def test_get_user_resumes():
    """Test get_user_resumes."""
    mock_db = Mock(spec=Session)
    mock_resumes = [Mock(spec=DatabaseResume), Mock(spec=DatabaseResume)]
    mock_db.query.return_value.filter.return_value.all.return_value = mock_resumes

    result = get_user_resumes(db=mock_db, user_id=1)

    assert result == mock_resumes
    mock_db.query.assert_called_once_with(DatabaseResume)
    assert mock_db.query.return_value.filter.call_count == 1
    mock_db.query.return_value.filter.return_value.all.assert_called_once()


@patch("resume_editor.app.api.routes.route_logic.resume_crud.DatabaseResume")
def test_create_resume_base_default(mock_db_resume):
    """Test create_resume creates a base resume by default."""
    mock_db = Mock(spec=Session)
    mock_instance = Mock()
    mock_db_resume.return_value = mock_instance

    result = create_resume(
        db=mock_db,
        user_id=1,
        name="Test Resume",
        content="Test Content",
    )

    mock_db_resume.assert_called_once_with(
        user_id=1,
        name="Test Resume",
        content="Test Content",
        is_base=True,
        parent_id=None,
        job_description=None,
    )
    mock_db.add.assert_called_once_with(mock_instance)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_instance)
    assert result == mock_instance


@patch("resume_editor.app.api.routes.route_logic.resume_crud.DatabaseResume")
def test_create_resume_refined(mock_db_resume):
    """Test create_resume for a refined resume."""
    mock_db = Mock(spec=Session)
    mock_instance = Mock()
    mock_db_resume.return_value = mock_instance

    result = create_resume(
        db=mock_db,
        user_id=1,
        name="Refined Resume",
        content="Refined Content",
        is_base=False,
        parent_id=123,
        job_description="A cool job",
    )

    mock_db_resume.assert_called_once_with(
        user_id=1,
        name="Refined Resume",
        content="Refined Content",
        is_base=False,
        parent_id=123,
        job_description="A cool job",
    )
    mock_db.add.assert_called_once_with(mock_instance)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_instance)
    assert result == mock_instance


def test_update_resume():
    """Test update_resume."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)

    result = update_resume(
        db=mock_db,
        resume=mock_resume,
        name="New Name",
        content="New Content",
    )

    assert mock_resume.name == "New Name"
    assert mock_resume.content == "New Content"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_resume)
    assert result == mock_resume


def test_update_resume_only_name():
    """Test update_resume with only name."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)
    mock_resume.content = "Initial Content"

    result = update_resume(db=mock_db, resume=mock_resume, name="New Name")

    assert result.name == "New Name"
    assert result.content == "Initial Content"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_resume)
    assert result == mock_resume


def test_update_resume_only_content():
    """Test update_resume with only content."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)
    mock_resume.name = "Initial Name"

    result = update_resume(db=mock_db, resume=mock_resume, content="New Content")

    assert result.name == "Initial Name"
    assert result.content == "New Content"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_resume)
    assert result == mock_resume


def test_delete_resume():
    """Test delete_resume."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)

    delete_resume(db=mock_db, resume=mock_resume)

    mock_db.delete.assert_called_once_with(mock_resume)
    mock_db.commit.assert_called_once()
