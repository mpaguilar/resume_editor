from datetime import date, datetime

import pytest

from resume_editor.app.api.routes.route_logic.resume_filtering import (
    filter_experience_by_date,
)
from resume_editor.app.api.routes.route_models import ExperienceResponse


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
    ]
    # Projects have a similar structure for date filtering
    projects_payload = [
        {  # 0: Before
            "overview": {"title": "P Before", "start_date": datetime(2018, 1, 1)},
            "description": {"text": "Project from before the date range."},
        },
        {  # 1: Inside
            "overview": {"title": "P Inside", "start_date": datetime(2020, 5, 1)},
            "description": {"text": "Project from within the date range."},
        },
        {  # 2: After
            "overview": {"title": "P After", "start_date": datetime(2022, 1, 1)},
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
    ]
    return ExperienceResponse(**create_payload(roles_payload, projects_payload))


def test_filter_no_dates(sample_experience):
    """Test that providing no dates results in no filtering."""
    result = filter_experience_by_date(sample_experience, None, None)
    assert len(result.roles) == 7
    assert len(result.projects) == 6


def test_filter_with_start_date(sample_experience):
    """Test filtering with only a start date."""
    start_date = date(2020, 1, 1)
    result = filter_experience_by_date(sample_experience, start_date, None)

    # Roles ending before start_date are excluded ('Before')
    assert len(result.roles) == 6
    assert "Before" not in [r.basics.company for r in result.roles]

    # Projects ending before start_date are excluded ('P Before', 'P With End Date Outside')
    project_titles = [p.overview.title for p in result.projects]
    assert len(result.projects) == 4
    assert "P Before" not in project_titles
    assert "P With End Date Outside" not in project_titles
    assert "P No Date" in project_titles


def test_filter_with_end_date(sample_experience):
    """Test filtering with only an end date."""
    end_date = date(2020, 12, 31)
    result = filter_experience_by_date(sample_experience, None, end_date)

    # Roles starting after end_date are excluded ('After')
    assert len(result.roles) == 6
    assert "After" not in [r.basics.company for r in result.roles]

    # Projects starting after end_date are excluded ('P After')
    project_titles = [p.overview.title for p in result.projects]
    assert len(result.projects) == 5
    assert "P After" not in project_titles
    assert "P No Date" in project_titles


def test_filter_with_full_date_range(sample_experience):
    """Test filtering with both a start and an end date."""
    start_date = date(2020, 1, 1)
    end_date = date(2020, 12, 31)
    result = filter_experience_by_date(sample_experience, start_date, end_date)

    # Expected roles to be included: Straddle Start, Inside, Straddle End, Ongoing Before, Ongoing During
    expected_companies = [
        "Straddle Start",
        "Inside",
        "Straddle End",
        "Ongoing Before",
        "Ongoing During",
    ]
    role_companies = [r.basics.company for r in result.roles]
    assert len(result.roles) == 5
    assert all(company in role_companies for company in expected_companies)

    # Expected projects: P Inside, P No Date, P With End Date Inside
    expected_projects = ["P Inside", "P No Date", "P With End Date Inside"]
    project_titles = [p.overview.title for p in result.projects]
    assert len(result.projects) == 3
    assert all(title in project_titles for title in expected_projects)
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
