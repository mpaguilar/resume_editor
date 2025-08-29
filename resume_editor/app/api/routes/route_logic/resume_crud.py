import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)


def get_resume_by_id_and_user(
    db: Session,
    resume_id: int,
    user_id: int,
) -> DatabaseResume:
    """
    Retrieve a resume by its ID and verify it belongs to the specified user.

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


def get_user_resumes(db: Session, user_id: int) -> list[DatabaseResume]:
    """
    Retrieve all resumes associated with a specific user.

    Args:
        db (Session): The SQLAlchemy database session used to query the database.
        user_id (int): The unique identifier for the user whose resumes are to be retrieved.

    Returns:
        list[DatabaseResume]: A list of DatabaseResume objects belonging to the specified user.

    Notes:
        1. Query the DatabaseResume table for all records where the user_id matches the provided user_id.
        2. Return the list of matching DatabaseResume objects.
        3. This function performs a single database query to retrieve all resumes for a user.

    """
    return db.query(DatabaseResume).filter(DatabaseResume.user_id == user_id).all()


def create_resume(db: Session, user_id: int, name: str, content: str) -> DatabaseResume:
    """
    Create and save a new resume.

    Args:
        db (Session): The database session.
        user_id (int): The ID of the user who owns the resume.
        name (str): The name of the resume.
        content (str): The content of the resume.

    Returns:
        DatabaseResume: The newly created resume object.

    Notes:
        1. Create a new DatabaseResume instance with the provided user_id, name, and content.
        2. Add the instance to the database session.
        3. Commit the transaction to persist the changes.
        4. Refresh the instance to ensure it has the latest state, including the generated ID.
        5. Return the created resume.
        6. This function performs a database write operation.

    """
    resume = DatabaseResume(user_id=user_id, name=name, content=content)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def update_resume(
    db: Session,
    resume: DatabaseResume,
    name: str | None = None,
    content: str | None = None,
) -> DatabaseResume:
    """
    Update a resume's name and/or content.

    Args:
        db (Session): The database session.
        resume (DatabaseResume): The resume to update.
        name (str, optional): The new name for the resume. If None, the name is not updated.
        content (str, optional): The new content for the resume. If None, the content is not updated.

    Returns:
        DatabaseResume: The updated resume object.

    Notes:
        1. If a new name is provided (not None), update the resume's name attribute.
        2. If new content is provided (not None), update the resume's content attribute.
        3. Commit the transaction to save the changes to the database.
        4. Refresh the resume object to ensure it reflects the latest state from the database.
        5. Return the updated resume.
        6. This function performs a database write operation.

    """
    if name is not None:
        resume.name = name
    if content is not None:
        resume.content = content
    db.commit()
    db.refresh(resume)
    return resume


def delete_resume(db: Session, resume: DatabaseResume) -> None:
    """
    Delete a resume.

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
