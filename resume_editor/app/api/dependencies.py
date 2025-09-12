import logging

from fastapi import Depends
from sqlalchemy.orm import Session

from resume_editor.app.api.routes.route_logic.resume_crud import (
    get_resume_by_id_and_user,
)
from resume_editor.app.core.auth import get_current_user_from_cookie
from resume_editor.app.database.database import get_db
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User

log = logging.getLogger(__name__)


async def get_resume_for_user(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
) -> DatabaseResume:
    """
    Dependency to get a specific resume for the current user.

    Args:
        resume_id (int): The unique identifier of the resume to retrieve.
        db (Session): The database session dependency.
        current_user (User): The current authenticated user.

    Returns:
        DatabaseResume: The resume object if found and belongs to the user.

    Raises:
        HTTPException: If the resume is not found or doesn't belong to the user.

    Notes:
        1. Queries the database for a resume with the given ID and user_id.
        2. If no resume is found, raises a 404 error from `get_resume_by_id_and_user`.
        3. Returns the resume object.

    """
    return get_resume_by_id_and_user(db, resume_id=resume_id, user_id=current_user.id)
