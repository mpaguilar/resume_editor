import logging

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
)
from resume_editor.app.models.resume_model import (
    ResumeData,
)

log = logging.getLogger(__name__)


class ResumeCreateParams(BaseModel):
    """Parameters for creating a resume."""

    user_id: int
    name: str
    content: str
    is_base: bool = True
    parent_id: int | None = None
    job_description: str | None = None
    introduction: str | None = None


class ResumeUpdateParams(BaseModel):
    """Parameters for updating a resume."""

    name: str | None = None
    content: str | None = None
    introduction: str | None = None
    notes: str | None = None


def get_resume_by_id_and_user(
    db: Session,
    resume_id: int,
    user_id: int,
) -> DatabaseResume:
    """Retrieve a resume by its ID and verify it belongs to the specified user.

    Args:
        db (Session): The SQLAlchemy database session used to query the database.
        resume_id (int): The unique identifier for the resume to retrieve.
        user_id (int): The unique identifier for the user who owns the resume.

    Returns:
        DatabaseResume: The resume object matching the provided ID and user ID.

    Raises:
        HTTPException: If no resume is found with the given ID and user ID, raises a 404 error with detail "Resume not found".

    Notes:
        1. Query the DatabaseResume table for a record where the id matches resume_id and the user_id matches user_id.
        2. If no matching record is found, raise an HTTPException with status code 404 and detail "Resume not found".
        3. Return the found DatabaseResume object.
        4. This function performs a single database query to retrieve a resume.

    """
    resume = (
        db.query(DatabaseResume)
        .filter(
            DatabaseResume.id == resume_id,
            DatabaseResume.user_id == user_id,
        )
        .first()
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    return resume


def get_user_resumes(
    db: Session,
    user_id: int,
    sort_by: str | None = None,
) -> list[DatabaseResume]:
    """Retrieve all resumes associated with a specific user, with optional sorting.

    Args:
        db (Session): The SQLAlchemy database session used to query the database.
        user_id (int): The unique identifier for the user whose resumes are to be retrieved.
        sort_by (str | None): The sorting criterion. Defaults to 'updated_at_desc'.

    Returns:
        list[DatabaseResume]: A sorted list of DatabaseResume objects belonging to the specified user.

    Notes:
        1. Build a query for records in the DatabaseResume table where the user_id matches.
        2. Determine the sorting column and direction from the `sort_by` parameter.
        3. Default to sorting by `updated_at` in descending order if `sort_by` is not provided.
        4. Apply the sorting to the query.
        5. Execute the query and return the list of matching DatabaseResume objects.
        6. This function performs a single database query.

    """
    query = db.query(DatabaseResume).filter(DatabaseResume.user_id == user_id)

    sort_criteria = sort_by or "updated_at_desc"

    if sort_criteria.endswith("_asc"):
        sort_key = sort_criteria[:-4]
        order_func = getattr(DatabaseResume, sort_key).asc()
    else:  # ends with _desc
        sort_key = sort_criteria[:-5]
        order_func = getattr(DatabaseResume, sort_key).desc()

    query = query.order_by(order_func)

    return query.all()


def create_resume(
    db: Session,
    params: ResumeCreateParams,
) -> DatabaseResume:
    """Create and save a new resume.

    Args:
        db (Session): The database session.
        params (ResumeCreateParams): The parameters required to create the resume.

    Returns:
        DatabaseResume: The newly created resume object.

    Notes:
        1. Create a new DatabaseResume instance with all provided details.
        2. Add the instance to the database session.
        3. Commit the transaction to persist the changes.
        4. Refresh the instance to ensure it has the latest state, including the generated ID.
        5. Return the created resume.
        6. This function performs a database write operation.

    """
    resume_data = ResumeData(
        user_id=params.user_id,
        name=params.name,
        content=params.content,
        is_base=params.is_base,
        parent_id=params.parent_id,
        job_description=params.job_description,
        introduction=params.introduction,
    )
    resume = DatabaseResume(data=resume_data)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def update_resume(
    db: Session,
    resume: DatabaseResume,
    params: ResumeUpdateParams,
) -> DatabaseResume:
    """Update a resume's name, content, introduction, and/or notes.

    Args:
        db (Session): The database session.
        resume (DatabaseResume): The resume to update.
        params (ResumeUpdateParams): The new data for the resume.

    Returns:
        DatabaseResume: The updated resume object.

    Notes:
        1. If a new name is provided (not None), update the resume's name attribute.
        2. If new content is provided (not None), update the resume's content attribute.
        3. If an introduction is provided (not None), update the resume's introduction attribute.
        4. If new notes are provided (not None), update the resume's notes attribute.
        5. Commit the transaction to save the changes to the database.
        6. Refresh the resume object to ensure it reflects the latest state from the database.
        7. Return the updated resume.
        8. This function performs a database write operation.

    """
    if params.name is not None:
        resume.name = params.name
    if params.content is not None:
        resume.content = params.content
    if params.introduction is not None:
        resume.introduction = params.introduction
    if params.notes is not None:
        resume.notes = params.notes
    db.commit()
    db.refresh(resume)
    return resume


def delete_resume(db: Session, resume: DatabaseResume) -> None:
    """Delete a resume.

    Args:
        db (Session): The database session.
        resume (DatabaseResume): The resume to delete.

    Returns:
        None

    Notes:
        1. Delete the resume object from the database session.
        2. Commit the transaction to persist the deletion.
        3. This function performs a database write operation.

    """
    db.delete(resume)
    db.commit()
