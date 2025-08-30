import logging
from datetime import date, datetime

from resume_editor.app.api.routes.route_models import ExperienceResponse

log = logging.getLogger(__name__)


def _get_date_from_optional_datetime(dt: datetime | None) -> date | None:
    """Extract the date portion from an optional datetime object.

    Args:
        dt (datetime | None): The datetime object to extract the date from, or None.

    Returns:
        date | None: The date portion of the datetime object, or None if input is None.

    Notes:
        1. If the input dt is None, return None.
        2. Otherwise, extract and return the date portion of the datetime object using the date() method.
    """
    return dt.date() if dt else None


def _is_in_date_range(
    item_start_date: date | None,
    item_end_date: date | None,
    filter_start_date: date | None,
    filter_end_date: date | None,
) -> bool:
    """Check if an item's date range overlaps with the filter's date range.

    Args:
        item_start_date (date | None): The start date of the item being evaluated.
        item_end_date (date | None): The end date of the item (or None if ongoing).
        filter_start_date (date | None): The start date of the filtering period.
        filter_end_date (date | None): The end date of the filtering period.

    Returns:
        bool: True if the item overlaps with the filter's date range, False otherwise.

    Notes:
        1. If the filter has a start date and the item ends before that date, the item is out of range.
        2. If the filter has an end date and the item starts after that date, the item is out of range.
        3. Otherwise, the item is considered to be in range.
    """
    # An item is considered OUT of range if it ends before the filter starts...
    if filter_start_date and item_end_date and item_end_date < filter_start_date:
        return False
    # ... or if it starts after the filter ends.
    if filter_end_date and item_start_date and item_start_date > filter_end_date:
        return False
    # Otherwise, it's in range.
    return True


def filter_experience_by_date(
    experience: ExperienceResponse,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ExperienceResponse:
    """Filter roles and projects in an ExperienceResponse based on a date range.

    Args:
        experience (ExperienceResponse): The experience data to filter.
        start_date (date | None): The start of the filtering period. If None, no start constraint is applied.
        end_date (date | None): The end of the filtering period. If None, no end constraint is applied.

    Returns:
        ExperienceResponse: A new ExperienceResponse object containing only roles and projects that overlap with the specified date range.

    Notes:
        1. If both start_date and end_date are None, return the original experience object unmodified.
        2. Iterate through the roles in the experience object and check if each role's date range overlaps with the filter range using _is_in_date_range.
        3. For each role that overlaps, add it to the filtered_roles list.
        4. Iterate through the projects in the experience object and check if each project's date range overlaps with the filter range.
        5. Projects without an end date are treated as single-day events occurring on their start date.
        6. For each project that overlaps, add it to the filtered_projects list.
        7. Return a new ExperienceResponse object with the filtered roles and projects.
    """
    if not start_date and not end_date:
        return experience

    filtered_roles = []
    if experience.roles:
        for role in experience.roles:
            role_start = _get_date_from_optional_datetime(
                getattr(role.basics, "start_date", None),
            )
            role_end = _get_date_from_optional_datetime(
                getattr(role.basics, "end_date", None),
            )
            if _is_in_date_range(role_start, role_end, start_date, end_date):
                filtered_roles.append(role)

    filtered_projects = []
    if experience.projects:
        for project in experience.projects:
            project_start = _get_date_from_optional_datetime(
                getattr(project.overview, "start_date", None),
            )
            project_end = _get_date_from_optional_datetime(
                getattr(project.overview, "end_date", None),
            )

            # Treat projects without an end date as point-in-time events
            if project_end is None:
                project_end = project_start
            if _is_in_date_range(project_start, project_end, start_date, end_date):
                filtered_projects.append(project)

    return ExperienceResponse(roles=filtered_roles, projects=filtered_projects)
