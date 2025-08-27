import logging
from datetime import date, datetime

from resume_editor.app.api.routes.route_models import ExperienceResponse

log = logging.getLogger(__name__)


def _get_date_from_optional_datetime(dt: datetime | None) -> date | None:
    """Safely convert an optional datetime object to an optional date object."""
    return dt.date() if dt else None


def _is_in_date_range(
    item_start_date: date | None,
    item_end_date: date | None,
    filter_start_date: date | None,
    filter_end_date: date | None,
) -> bool:
    """Check if an item's date range overlaps with the filter's date range.

    Args:
        item_start_date (date | None): Start date of the item.
        item_end_date (date | None): End date of the item (or None if ongoing).
        filter_start_date (date | None): Start date of the filter period.
        filter_end_date (date | None): End date of the filter period.

    Returns:
        bool: True if the item overlaps with the date range, False otherwise.
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
        start_date (date | None): The start of the filtering period.
        end_date (date | None): The end of the filtering period.

    Returns:
        ExperienceResponse: A new ExperienceResponse with filtered roles and projects.

    Notes:
        1. If no start_date or end_date is provided, returns the original experience object.
        2. Filters the list of roles, keeping those that overlap with the date range.
        3. Filters the list of projects, keeping those that overlap with the date range.
        4. An item is considered within the range if its own date range has any overlap with the filter's date range.
        5. Ongoing items (no end date) are included if their start date is before the filter's end date (or if there is no filter end date).
        6. Projects without an end date are treated as single-day events occurring on their start date.
    """
    if not start_date and not end_date:
        return experience

    filtered_roles = []
    if experience.roles:
        for role in experience.roles:
            role_start = _get_date_from_optional_datetime(
                getattr(role.basics, "start_date", None)
            )
            role_end = _get_date_from_optional_datetime(
                getattr(role.basics, "end_date", None)
            )
            if _is_in_date_range(role_start, role_end, start_date, end_date):
                filtered_roles.append(role)

    filtered_projects = []
    if experience.projects:
        for project in experience.projects:
            project_start = _get_date_from_optional_datetime(
                getattr(project.overview, "start_date", None)
            )
            project_end = _get_date_from_optional_datetime(
                getattr(project.overview, "end_date", None)
            )

            # Treat projects without an end date as point-in-time events
            if project_end is None:
                project_end = project_start
            if _is_in_date_range(project_start, project_end, start_date, end_date):
                filtered_projects.append(project)

    return ExperienceResponse(roles=filtered_roles, projects=filtered_projects)
