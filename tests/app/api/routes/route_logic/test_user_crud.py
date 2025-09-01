import logging
from unittest.mock import MagicMock

from resume_editor.app.api.routes.route_logic.user_crud import user_count
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


def test_user_count_with_users():
    """
    Test user_count when users exist in the database.
    """
    _msg = "test_user_count_with_users starting"
    log.debug(_msg)
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 5

    count = user_count(db=mock_db)

    assert count == 5
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.count.assert_called_once()
    _msg = "test_user_count_with_users returning"
    log.debug(_msg)


def test_user_count_with_no_users():
    """
    Test user_count when no users exist in the database.
    """
    _msg = "test_user_count_with_no_users starting"
    log.debug(_msg)
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0

    count = user_count(db=mock_db)

    assert count == 0
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.count.assert_called_once()
    _msg = "test_user_count_with_no_users returning"
    log.debug(_msg)
