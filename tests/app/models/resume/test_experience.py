from datetime import datetime

from resume_editor.app.models.resume.experience import (
    InclusionStatus,
    ProjectOverview,
    RoleBasics,
)


def test_role_basics_inclusion_status_default():
    """Test that RoleBasics has inclusion_status with a default of INCLUDE."""
    basics = RoleBasics(company="Test Co", title="Tester", start_date=datetime(2022, 1, 1))
    assert hasattr(basics, "inclusion_status")
    assert basics.inclusion_status == InclusionStatus.INCLUDE


def test_project_overview_inclusion_status_default():
    """Test that ProjectOverview has inclusion_status with a default of INCLUDE."""
    overview = ProjectOverview(title="Test Project")
    assert hasattr(overview, "inclusion_status")
    assert overview.inclusion_status == InclusionStatus.INCLUDE


def test_role_basics_can_set_inclusion_status():
    """Test setting a non-default inclusion_status on RoleBasics."""
    basics = RoleBasics(
        company="Test Co",
        title="Tester",
        start_date=datetime(2022, 1, 1),
        inclusion_status=InclusionStatus.OMIT,
    )
    assert basics.inclusion_status == InclusionStatus.OMIT


def test_project_overview_can_set_inclusion_status():
    """Test setting a non-default inclusion_status on ProjectOverview."""
    overview = ProjectOverview(
        title="Test Project", inclusion_status=InclusionStatus.NOT_RELEVANT
    )
    assert overview.inclusion_status == InclusionStatus.NOT_RELEVANT
