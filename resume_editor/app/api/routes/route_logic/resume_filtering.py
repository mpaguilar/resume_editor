import logging
from datetime import date, datetime
from typing import Any

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
        3. Otherwise, the item is considered to be in range. This includes ongoing items (those with no end date).

    """
    # An item is considered OUT of range if it ends before the filter starts...
    if filter_start_date and item_end_date and item_end_date < filter_start_date:
        return False
    # ... or if it starts after the filter ends.
    if filter_end_date and item_start_date and item_start_date > filter_end_date:
        return False
    # Otherwise, it's in range.
    return True


def _parse_role_dates(role: any) -> tuple[date | None, date | None]:
    """Parse start and end dates from a role object.

    Args:
        role: The role object containing basics with start_date and end_date.

    Returns:
        tuple[date | None, date | None]: A tuple of (start_date, end_date).

    Notes:
        1. Extract start_date from role.basics if available.
        2. Extract end_date from role.basics if available.
        3. Convert datetime objects to date objects.

    """
    if not role.basics:
        return None, None
    role_start = _get_date_from_optional_datetime(role.basics.start_date)
    role_end = _get_date_from_optional_datetime(role.basics.end_date)
    return role_start, role_end


def _parse_project_dates(project: any) -> tuple[date | None, date | None]:
    """Parse start and end dates from a project object.

    Args:
        project: The project object containing overview with start_date and end_date.

    Returns:
        tuple[date | None, date | None]: A tuple of (start_date, end_date).

    Notes:
        1. Extract start_date from project.overview if available.
        2. Extract end_date from project.overview if available.
        3. Convert datetime objects to date objects.

    """
    if not project.overview:
        return None, None
    project_start = _get_date_from_optional_datetime(project.overview.start_date)
    project_end = _get_date_from_optional_datetime(project.overview.end_date)
    return project_start, project_end


def _filter_items_by_date_range(
    items: list[Any],
    date_parser: callable,
    start_date: date | None,
    end_date: date | None,
) -> list[Any]:
    """Filter a list of items based on their date ranges.

    Args:
        items: The list of items to filter.
        date_parser: A function that extracts (start_date, end_date) from an item.
        start_date (date | None): The start of the filtering period.
        end_date (date | None): The end of the filtering period.

    Returns:
        list[Any]: A list of items that overlap with the date range.

    Notes:
        1. Iterate through each item in the list.
        2. Parse the item's start and end dates using date_parser.
        3. Check if the item's date range overlaps with the filter range.
        4. Add items that overlap to the filtered list.

    """
    filtered = []
    for item in items:
        item_start, item_end = date_parser(item)
        if _is_in_date_range(item_start, item_end, start_date, end_date):
            filtered.append(item)
    return filtered


def filter_experience_by_date(
    experience: ExperienceResponse,
    start_date: date | None,
    end_date: date | None,
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
        2. Filter roles using _filter_items_by_date_range with _parse_role_dates.
        3. Filter projects using _filter_items_by_date_range with _parse_project_dates.
        4. Return a new ExperienceResponse object with the filtered roles and projects.

    """
    _msg = f"filter_experience_by_date starting: start={start_date}, end={end_date}"
    log.debug(_msg)
    if not start_date and not end_date:
        log.debug("filter_experience_by_date returning: no dates, returning original.")
        return experience

    filtered_roles = []
    if experience.roles:
        filtered_roles = _filter_items_by_date_range(
            experience.roles,
            _parse_role_dates,
            start_date,
            end_date,
        )

    filtered_projects = []
    if experience.projects:
        filtered_projects = _filter_items_by_date_range(
            experience.projects,
            _parse_project_dates,
            start_date,
            end_date,
        )

    _msg = f"filter_experience_by_date returning: {len(filtered_roles)} roles, {len(filtered_projects)} projects"
    log.debug(_msg)
    return ExperienceResponse(roles=filtered_roles, projects=filtered_projects)
