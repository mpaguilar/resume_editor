import logging
from datetime import datetime

import pendulum
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query, Session

from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
)
from resume_editor.app.models.resume_model import (
    ResumeData,
)

log = logging.getLogger(__name__)


class DateRange(BaseModel):
    """Represents a date range for pagination.

    Attributes:
        start_date: The start date of the range (inclusive).
        end_date: The end date of the range (inclusive).

    """

    start_date: datetime
    end_date: datetime


class ResumeFilterParams(BaseModel):
    """Parameters for filtering resumes.

    Attributes:
        search_query: The search query string (max 100 chars).
        date_range: Optional date range to filter by.

    """

    search_query: str | None = None
    date_range: DateRange | None = None


class ResumeCreateParams(BaseModel):
    """Parameters for creating a resume."""

    user_id: int
    name: str
    content: str
    is_base: bool = True
    parent_id: int | None = None
    job_description: str | None = None
    introduction: str | None = None
    company: str | None = None
    notes: str | None = None


class ResumeUpdateParams(BaseModel):
    """Parameters for updating a resume."""

    name: str | None = None
    content: str | None = None
    introduction: str | None = None
    notes: str | None = None
    company: str | None = None


def get_week_range(week_offset: int = 0) -> DateRange:
    """Calculate start and end dates for a given week offset.

    Args:
        week_offset: Number of weeks to offset from current week.
                    0 = current week (last 7 days from now),
                    -1 = previous week,
                    1 = next week (future).

    Returns:
        DateRange: Object containing start_date and end_date for the week.
                   End date is now minus (week_offset * 7) days.
                   Start date is 7 days before end date.

    Notes:
        1. Uses pendulum for date calculations to handle timezones correctly.
        2. End date represents the "present" point for the given week offset.
        3. Start date is always 7 days before end date.
        4. Returns naive datetime objects for SQLAlchemy compatibility.

    """
    _msg = "get_week_range starting with week_offset=%s"
    log.debug(_msg, week_offset)

    now = pendulum.now()

    # End date is now minus (week_offset * 7) days
    end = now.add(weeks=week_offset)
    # Start date is 7 days before end
    start = end.subtract(days=7)

    # Convert to naive datetime for SQLAlchemy compatibility
    result = DateRange(
        start_date=start.naive(),
        end_date=end.naive(),
    )

    _msg = "get_week_range returning range: %s to %s"
    log.debug(_msg, result.start_date, result.end_date)
    return result


def get_oldest_resume_date(db: Session, user_id: int) -> datetime | None:
    """Get the oldest resume creation date for a user.

    Args:
        db: The SQLAlchemy database session.
        user_id: The ID of the user to query.

    Returns:
        datetime | None: The oldest created_at date, or None if no resumes exist.

    Notes:
        1. Queries DatabaseResume table for records matching user_id.
        2. Uses func.min() to get the earliest created_at timestamp.
        3. Returns None if user has no resumes.
        4. This function performs a single database query.

    """
    _msg = "get_oldest_resume_date starting for user_id=%s"
    log.debug(_msg, user_id)

    result = (
        db.query(func.min(DatabaseResume.created_at))
        .filter(DatabaseResume.user_id == user_id)
        .scalar()
    )

    _msg = "get_oldest_resume_date returning: %s"
    log.debug(_msg, result)
    return result


def apply_resume_filter(
    query: Query,
    search_query: str | None,
) -> Query:
    """Apply search filter to a resume query.

    Args:
        query: The SQLAlchemy query object to filter.
        search_query: The search query string. Supports multiple terms with AND logic.
                     Max 100 characters. Case-insensitive partial matching.

    Returns:
        object: The filtered query object.

    Notes:
        1. Truncates search query to 100 characters for security.
        2. Splits query into terms by whitespace.
        3. Each term must match either name OR notes OR company (case-insensitive, partial).
        4. All terms must match (AND logic between terms).
        5. Uses SQLAlchemy ilike for case-insensitive matching.
        6. This function does not execute the query.

    """
    _msg = "apply_resume_filter starting with search_query=%s"
    log.debug(_msg, search_query)

    if not search_query:
        _msg = "apply_resume_filter returning unfiltered query (no search query)"
        log.debug(_msg)
        return query

    # Truncate to max 100 characters
    search_query = search_query[:100]

    # Split into terms
    terms = search_query.split()

    if not terms:
        _msg = "apply_resume_filter returning unfiltered query (empty terms)"
        log.debug(_msg)
        return query

    # Build filter conditions - each term must match name OR notes OR company
    term_conditions = []
    for term in terms:
        term_pattern = f"%{term}%"
        term_filter = or_(
            DatabaseResume.name.ilike(term_pattern),
            DatabaseResume.notes.ilike(term_pattern),
            DatabaseResume.company.ilike(term_pattern),
        )
        term_conditions.append(term_filter)

    # All terms must match (AND logic)
    query = query.filter(and_(*term_conditions))

    _msg = "apply_resume_filter returning filtered query with %s terms"
    log.debug(_msg, len(terms))
    return query


def get_user_resumes_with_pagination(
    db: Session,
    user_id: int,
    week_offset: int = 0,
    search_query: str | None = None,
    sort_by: str | None = None,
) -> tuple[list[DatabaseResume], DateRange]:
    """Retrieve resumes with pagination and optional filtering.

    Args:
        db: The SQLAlchemy database session.
        user_id: The ID of the user whose resumes to retrieve.
        week_offset: Number of weeks to offset from current week (default: 0).
        search_query: Optional search query to filter resumes by name/notes.
        sort_by: The sorting criterion (e.g., 'updated_at_desc', 'name_asc').

    Returns:
        tuple[list[DatabaseResume], DateRange]: A tuple containing:
            - List of filtered/sorted resumes for the date range
            - The DateRange used for the query

    Notes:
        1. Calculates date range using get_week_range(week_offset).
        2. Base resumes are always included regardless of date range.
        3. Refined resumes are filtered by date range.
        4. If search_query is provided, refined resumes are additionally filtered
           by name/notes (case-insensitive, partial match, AND logic).
        5. Results are sorted according to sort_by parameter.
        6. This function performs database queries to retrieve resumes.

    """
    _msg = "get_user_resumes_with_pagination starting for user_id=%s week_offset=%s"
    log.debug(_msg, user_id, week_offset)

    # Get date range for this week offset
    date_range = get_week_range(week_offset)

    # Build base query for this user's resumes
    query = db.query(DatabaseResume).filter(DatabaseResume.user_id == user_id)

    # Base resumes are always included
    base_query = query.filter(DatabaseResume.is_base.is_(True))

    # Refined resumes filtered by date range
    refined_query = query.filter(
        DatabaseResume.is_base.is_(False),
        DatabaseResume.created_at >= date_range.start_date,
        DatabaseResume.created_at <= date_range.end_date,
    )

    # Apply search filter to refined resumes only if provided
    if search_query:
        refined_query = apply_resume_filter(refined_query, search_query)

    # Apply sorting
    sort_criteria = sort_by or "updated_at_desc"
    if sort_criteria.endswith("_asc"):
        sort_key = sort_criteria[:-4]
        order_func = getattr(DatabaseResume, sort_key).asc()
    else:  # ends with _desc
        sort_key = sort_criteria[:-5]
        order_func = getattr(DatabaseResume, sort_key).desc()

    base_query = base_query.order_by(DatabaseResume.updated_at.desc())
    refined_query = refined_query.order_by(order_func)

    # Execute queries
    base_resumes = base_query.all()
    refined_resumes = refined_query.all()

    # Combine results
    all_resumes = base_resumes + refined_resumes

    _msg = "get_user_resumes_with_pagination returning %s resumes"
    log.debug(_msg, len(all_resumes))
    return all_resumes, date_range


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
        company=params.company,
        notes=params.notes,
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
    if params.company is not None:
        resume.company = params.company
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
