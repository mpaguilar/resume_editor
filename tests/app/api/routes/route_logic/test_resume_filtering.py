from datetime import date, datetime

import pytest

from resume_editor.app.api.routes.route_logic.resume_filtering import (
    _get_date_from_optional_datetime,
    _is_in_date_range,
    filter_experience_by_date,
)
from resume_editor.app.api.routes.route_models import ExperienceResponse


def test_get_date_from_optional_datetime():
    """Test _get_date_from_optional_datetime helper function."""
    # Test with a datetime object
    dt = datetime(2023, 10, 27, 10, 30)
    assert _get_date_from_optional_datetime(dt) == date(2023, 10, 27)

    # Test with None
    assert _get_date_from_optional_datetime(None) is None


@pytest.mark.parametrize(
    "item_start, item_end, filter_start, filter_end, expected",
    [
        # Item completely within filter range
        (date(2023, 2, 1), date(2023, 3, 1), date(2023, 1, 1), date(2023, 4, 1), True),
        # Item overlaps at the start
        (date(2022, 12, 1), date(2023, 1, 15), date(2023, 1, 1), date(2023, 2, 1), True),
        # Item overlaps at the end
        (date(2023, 3, 15), date(2023, 4, 15), date(2023, 3, 1), date(2023, 4, 1), True),
        # Item surrounds filter range
        (date(2022, 1, 1), date(2024, 1, 1), date(2023, 1, 1), date(2023, 2, 1), True),
        # Item completely before filter range
        (
            date(2022, 1, 1),
            date(2022, 12, 31),
            date(2023, 1, 1),
            date(2023, 2, 1),
            False,
        ),
        # Item completely after filter range
        (date(2023, 3, 1), date(2023, 4, 1), date(2023, 1, 1), date(2023, 2, 1), False),
        # Item ends on filter start date
        (date(2022, 12, 1), date(2023, 1, 1), date(2023, 1, 1), date(2023, 2, 1), True),
        # Item starts on filter end date
        (date(2023, 2, 1), date(2023, 3, 1), date(2023, 1, 1), date(2023, 2, 1), True),
        # No item dates
        (None, None, date(2023, 1, 1), date(2023, 2, 1), True),
        # Ongoing item that starts before filter and continues
        (date(2022, 1, 1), None, date(2023, 1, 1), date(2023, 2, 1), True),
        # Ongoing item that starts within filter range
        (date(2023, 1, 15), None, date(2023, 1, 1), date(2023, 2, 1), True),
        # Ongoing item that starts after filter range
        (date(2023, 3, 1), None, date(2023, 1, 1), date(2023, 2, 1), False),
        # No filter dates
        (date(2023, 1, 1), date(2023, 2, 1), None, None, True),
        # Only filter start date, item is after
        (date(2023, 2, 1), date(2023, 3, 1), date(2023, 1, 1), None, True),
        # Only filter start date, item ends before
        (date(2022, 1, 1), date(2022, 12, 31), date(2023, 1, 1), None, False),
        # Only filter end date, item is before
        (date(2022, 1, 1), date(2022, 12, 31), None, date(2023, 1, 1), True),
        # Only filter end date, item is after
        (date(2023, 2, 1), date(2023, 3, 1), None, date(2023, 1, 1), False),
        # Point-in-time event within range
        (
            date(2023, 1, 15),
            date(2023, 1, 15),
            date(2023, 1, 1),
            date(2023, 2, 1),
            True,
        ),
        # Point-in-time event before range
        (
            date(2022, 12, 31),
            date(2022, 12, 31),
            date(2023, 1, 1),
            date(2023, 2, 1),
            False,
        ),
        # Point-in-time event after range
        (date(2023, 2, 2), date(2023, 2, 2), date(2023, 1, 1), date(2023, 2, 1), False),
    ],
)
def test_is_in_date_range(item_start, item_end, filter_start, filter_end, expected):
    """Test _is_in_date_range with various scenarios."""
    assert _is_in_date_range(item_start, item_end, filter_start, filter_end) == expected


def create_payload(roles=None, projects=None):
    """Helper to create an ExperienceResponse-compatible payload."""
    return {"roles": roles or [], "projects": projects or []}


@pytest.fixture
def sample_experience():
    """Fixture with a sample set of roles and projects for filtering tests."""
    roles_payload = [
        {  # 0: Before range
            "basics": {
                "company": "Before",
                "title": "dev",
                "start_date": datetime(2019, 1, 1),
                "end_date": datetime(2019, 12, 31),
            },
        },
        {  # 1: Straddles start of range
            "basics": {
                "company": "Straddle Start",
                "title": "dev",
                "start_date": datetime(2019, 6, 1),
                "end_date": datetime(2020, 6, 30),
            },
        },
        {  # 2: Fully inside range
            "basics": {
                "company": "Inside",
                "title": "dev",
                "start_date": datetime(2020, 2, 1),
                "end_date": datetime(2020, 11, 30),
            },
        },
        {  # 3: Straddles end of range
            "basics": {
                "company": "Straddle End",
                "title": "dev",
                "start_date": datetime(2020, 8, 1),
                "end_date": datetime(2021, 2, 28),
            },
        },
        {  # 4: After range
            "basics": {
                "company": "After",
                "title": "dev",
                "start_date": datetime(2021, 5, 1),
                "end_date": datetime(2021, 12, 31),
            },
        },
        {  # 5: Ongoing, started before range
            "basics": {
                "company": "Ongoing Before",
                "title": "dev",
                "start_date": datetime(2019, 10, 1),
                "end_date": None,
            },
        },
        {  # 6: Ongoing, started during range
            "basics": {
                "company": "Ongoing During",
                "title": "dev",
                "start_date": datetime(2020, 10, 1),
                "end_date": None,
            },
        },
        {  # 7: No basics
            "basics": None,
            "summary": {
                "text": "This role has no basics and should always be included in filtered results."
            },
        },
    ]
    # Projects have a similar structure for date filtering
    projects_payload = [
        {  # 0: Before range - point in time
            "overview": {
                "title": "P Before",
                "start_date": datetime(2018, 1, 1),
                "end_date": datetime(2018, 1, 1),
            },
            "description": {"text": "Project from before the date range."},
        },
        {  # 1: Inside range - point in time
            "overview": {
                "title": "P Inside",
                "start_date": datetime(2020, 5, 1),
                "end_date": datetime(2020, 5, 1),
            },
            "description": {"text": "Project from within the date range."},
        },
        {  # 2: After range - point in time
            "overview": {
                "title": "P After",
                "start_date": datetime(2022, 1, 1),
                "end_date": datetime(2022, 1, 1),
            },
            "description": {"text": "Project from after the date range."},
        },
        {  # 3: No start date
            "overview": {"title": "P No Date", "start_date": None},
            "description": {"text": "Project with no date."},
        },
        {  # 4: Has end_date, outside range
            "overview": {
                "title": "P With End Date Outside",
                "start_date": datetime(2019, 1, 1),
                "end_date": datetime(2019, 6, 30),
            },
            "description": {"text": "Project with end date outside range."},
        },
        {  # 5: Has end_date, inside range
            "overview": {
                "title": "P With End Date Inside",
                "start_date": datetime(2020, 1, 15),
                "end_date": datetime(2020, 2, 15),
            },
            "description": {"text": "Project with end date inside range."},
        },
        {  # 6: Ongoing, started before range
            "overview": {
                "title": "P Ongoing Before",
                "start_date": datetime(2019, 10, 1),
                "end_date": None,
            },
            "description": {"text": "Ongoing project started before range"},
        },
        {  # 7: Ongoing, started during range
            "overview": {
                "title": "P Ongoing During",
                "start_date": datetime(2020, 10, 1),
                "end_date": None,
            },
            "description": {"text": "Ongoing project started during range"},
        },
        {  # 8: No overview
            "overview": None,
            "description": {"text": "Project with no overview."},
        },
    ]
    return ExperienceResponse(**create_payload(roles_payload, projects_payload))


def test_filter_no_dates(sample_experience):
    """Test that providing no dates results in no filtering."""
    result = filter_experience_by_date(sample_experience, None, None)
    assert len(result.roles) == 8
    assert len(result.projects) == 9


def test_filter_with_start_date(sample_experience):
    """Test filtering with only a start date."""
    start_date = date(2020, 1, 1)
    result = filter_experience_by_date(sample_experience, start_date, None)

    # Roles ending before start_date are excluded ('Before')
    expected_companies = {
        "Straddle Start",
        "Inside",
        "Straddle End",
        "After",
        "Ongoing Before",
        "Ongoing During",
    }
    role_companies = {r.basics.company for r in result.roles if r.basics}
    assert len(result.roles) == 7  # 6 with basics + 1 without
    assert len(role_companies) == 6
    assert role_companies == expected_companies
    assert any(r.basics is None for r in result.roles)

    # Projects ending before start_date are excluded ('P Before', 'P With End Date Outside')
    expected_projects = {
        "P Inside",
        "P After",
        "P No Date",
        "P With End Date Inside",
        "P Ongoing Before",
        "P Ongoing During",
    }
    project_titles = {p.overview.title for p in result.projects if p.overview}
    assert len(result.projects) == 7  # 6 with overview + 1 without
    assert len(project_titles) == 6
    assert project_titles == expected_projects
    assert any(p.overview is None for p in result.projects)


def test_filter_with_end_date(sample_experience):
    """Test filtering with only an end date."""
    end_date = date(2020, 12, 31)
    result = filter_experience_by_date(sample_experience, None, end_date)

    # Roles starting after end_date are excluded ('After')
    expected_companies = {
        "Before",
        "Straddle Start",
        "Inside",
        "Straddle End",
        "Ongoing Before",
        "Ongoing During",
    }
    role_companies = {r.basics.company for r in result.roles if r.basics}
    assert len(result.roles) == 7  # 6 with basics + 1 without
    assert len(role_companies) == 6
    assert role_companies == expected_companies
    assert any(r.basics is None for r in result.roles)

    # Projects starting after end_date are excluded ('P After')
    expected_projects = {
        "P Before",
        "P Inside",
        "P No Date",
        "P With End Date Outside",
        "P With End Date Inside",
        "P Ongoing Before",
        "P Ongoing During",
    }
    project_titles = {p.overview.title for p in result.projects if p.overview}
    assert len(result.projects) == 8  # 7 with overview + 1 without
    assert len(project_titles) == 7
    assert project_titles == expected_projects
    assert any(p.overview is None for p in result.projects)


def test_filter_with_full_date_range(sample_experience):
    """Test filtering with both a start and an end date."""
    start_date = date(2020, 1, 1)
    end_date = date(2020, 12, 31)
    result = filter_experience_by_date(sample_experience, start_date, end_date)

    # Expected roles to be included: Straddle Start, Inside, Straddle End, Ongoing Before, Ongoing During, and Role with no basics
    expected_companies = [
        "Straddle Start",
        "Inside",
        "Straddle End",
        "Ongoing Before",
        "Ongoing During",
    ]
    role_companies = [r.basics.company for r in result.roles if r.basics]
    assert len(result.roles) == 6
    assert len(role_companies) == 5
    assert all(company in role_companies for company in expected_companies)
    assert any(r.basics is None for r in result.roles)

    # Expected projects: P Inside, P No Date, P With End Date Inside, P Ongoing Before, P Ongoing During, and project with no overview
    expected_projects = [
        "P Inside",
        "P No Date",
        "P With End Date Inside",
        "P Ongoing Before",
        "P Ongoing During",
    ]
    project_titles = [p.overview.title for p in result.projects if p.overview]
    assert len(result.projects) == 6
    assert len(project_titles) == 5
    assert all(title in project_titles for title in expected_projects)
    assert any(p.overview is None for p in result.projects)
    assert all(
        title not in project_titles
        for title in ["P Before", "P After", "P With End Date Outside"]
    )


def test_filter_with_empty_experience():
    """Test that filtering an empty experience object works correctly."""
    empty_experience = ExperienceResponse(**create_payload())
    start_date = date(2020, 1, 1)
    result = filter_experience_by_date(empty_experience, start_date, None)
    assert len(result.roles) == 0
    assert len(result.projects) == 0
