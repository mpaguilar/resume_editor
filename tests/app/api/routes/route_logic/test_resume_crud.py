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
    update_resume_notes,
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


import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def db_session_and_engine():
    """Create an in-memory SQLite database session for tests."""
    engine = create_engine("sqlite:///:memory:")
    DatabaseResume.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield SessionLocal, engine

    DatabaseResume.metadata.drop_all(bind=engine)


@pytest.fixture
def db_with_resumes(db_session_and_engine):
    """Fixture to provide a db session with pre-populated resumes."""
    SessionLocal, _ = db_session_and_engine
    db = SessionLocal()

    now = datetime.datetime.now(datetime.UTC)
    user_id = 1

    # Create resumes with different timestamps and names
    r_gamma = DatabaseResume(user_id=user_id, name="gamma", content="c")
    r_beta = DatabaseResume(user_id=user_id, name="beta", content="c")
    r_alpha = DatabaseResume(user_id=user_id, name="alpha", content="c")
    # Resume for another user to ensure filtering works
    r_delta = DatabaseResume(user_id=2, name="delta", content="c")

    db.add_all([r_gamma, r_beta, r_alpha, r_delta])
    db.commit()  # Committing assigns IDs and default timestamps

    # Manually set timestamps for predictable sorting
    r_gamma.created_at = now
    r_gamma.updated_at = now - datetime.timedelta(days=1)

    r_beta.created_at = now - datetime.timedelta(days=1)
    r_beta.updated_at = now

    r_alpha.created_at = now - datetime.timedelta(days=2)
    r_alpha.updated_at = now - datetime.timedelta(days=2)

    db.commit()

    ids = {"alpha": r_alpha.id, "beta": r_beta.id, "gamma": r_gamma.id}

    try:
        yield db, ids
    finally:
        db.query(DatabaseResume).delete()
        db.commit()
        db.close()


@pytest.mark.parametrize(
    "sort_by, expected_order_names",
    [
        (None, ["beta", "gamma", "alpha"]),  # default updated_at_desc
        ("updated_at_desc", ["beta", "gamma", "alpha"]),
        ("updated_at_asc", ["alpha", "gamma", "beta"]),
        ("name_asc", ["alpha", "beta", "gamma"]),
        ("name_desc", ["gamma", "beta", "alpha"]),
        ("created_at_asc", ["alpha", "beta", "gamma"]),
        ("created_at_desc", ["gamma", "beta", "alpha"]),
    ],
)
def test_get_user_resumes_sorting_integration(
    db_with_resumes, sort_by, expected_order_names
):
    """Test get_user_resumes with sorting against a database session."""
    db, ids = db_with_resumes
    expected_order_ids = [ids[name] for name in expected_order_names]
    user_id = 1

    resumes = get_user_resumes(db=db, user_id=user_id, sort_by=sort_by)

    assert len(resumes) == 3
    assert [r.id for r in resumes] == expected_order_ids
    for resume in resumes:
        assert resume.user_id == user_id


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
        introduction=None,
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
        introduction=None,
    )
    mock_db.add.assert_called_once_with(mock_instance)
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_instance)
    assert result == mock_instance


@patch("resume_editor.app.api.routes.route_logic.resume_crud.DatabaseResume")
def test_create_resume_with_introduction(mock_db_resume):
    """Test create_resume with an introduction."""
    mock_db = Mock(spec=Session)
    mock_instance = Mock()
    mock_db_resume.return_value = mock_instance

    intro_text = "This is a great introduction."
    result = create_resume(
        db=mock_db,
        user_id=1,
        name="Resume With Intro",
        content="Some content",
        introduction=intro_text,
    )

    mock_db_resume.assert_called_once_with(
        user_id=1,
        name="Resume With Intro",
        content="Some content",
        is_base=True,
        parent_id=None,
        job_description=None,
        introduction=intro_text,
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
        introduction="New Intro",
    )

    assert mock_resume.name == "New Name"
    assert mock_resume.content == "New Content"
    assert mock_resume.introduction == "New Intro"
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


def test_update_resume_only_introduction():
    """Test update_resume with only introduction."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)
    mock_resume.name = "Initial Name"
    mock_resume.content = "Initial Content"

    result = update_resume(db=mock_db, resume=mock_resume, introduction="New Intro")

    assert result.name == "Initial Name"
    assert result.content == "Initial Content"
    assert result.introduction == "New Intro"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_resume)
    assert result == mock_resume


@pytest.mark.parametrize(
    "new_notes",
    [
        ("These are some new notes."),
        (None),
    ],
)
def test_update_resume_notes(new_notes):
    """Test update_resume_notes correctly updates notes."""
    mock_db = Mock(spec=Session)
    mock_resume = Mock(spec=DatabaseResume)
    mock_resume.notes = "Initial notes."

    result = update_resume_notes(db=mock_db, resume=mock_resume, notes=new_notes)

    assert mock_resume.notes == new_notes
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_resume)
    assert result == mock_resume
