from datetime import datetime

import pytest
from pydantic import ValidationError

from resume_editor.app.models.resume.experience import (
    Experience,
    Project,
    ProjectDescription,
    ProjectOverview,
    Projects,
    ProjectSkills,
    Role,
    RoleBasics,
    RoleResponsibilities,
    Roles,
    RoleSkills,
    RoleSummary,
)


class TestExperienceModels:
    """Test cases for experience models."""

    def test_role_summary_non_string(self):
        """Test that non-string summary values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleSummary(text=123)

    def test_role_responsibilities_non_string(self):
        """Test that non-string text values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleResponsibilities(text=123)

    def test_role_skills_non_list(self):
        """Test that non-list skills values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            RoleSkills(skills="not a list")

    def test_role_skills_list_with_non_string(self):
        """Test that list with non-string values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleSkills(skills=[123])

    def test_role_skills_iter(self):
        """Test iterating over RoleSkills."""
        # missing test
        skills = ["Python", "JavaScript"]
        role_skills = RoleSkills(skills=skills)
        assert [skill for skill in role_skills] == skills

    def test_role_basics_creation(self):
        """Test RoleBasics model creation."""
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2022, 12, 31)
        basics = RoleBasics(
            company="Tech Corp",
            start_date=start_date,
            end_date=end_date,
            title="Software Engineer",
        )
        assert basics.company == "Tech Corp"
        assert basics.start_date == start_date
        assert basics.end_date == end_date
        assert basics.title == "Software Engineer"

    def test_role_skills_creation(self):
        """Test RoleSkills model creation."""
        skills = RoleSkills(skills=["Python", "JavaScript", "SQL"])
        assert len(skills) == 3
        assert skills[0] == "Python"
        assert skills[1] == "JavaScript"
        assert skills[2] == "SQL"

    def test_role_skills_cleaning(self):
        """Test RoleSkills cleaning of input."""
        skills = RoleSkills(skills=[" Python ", "", "JavaScript ", "  ", "SQL"])
        assert len(skills) == 3
        assert skills[0] == "Python"
        assert skills[1] == "JavaScript"
        assert skills[2] == "SQL"

    def test_role_creation(self):
        """Test Role model creation."""
        basics = RoleBasics(
            company="Tech Corp",
            start_date=datetime(2020, 1, 1),
            title="Software Engineer",
        )
        summary = RoleSummary(text="Developed web applications")
        role = Role(basics=basics, summary=summary)
        assert role.basics == basics
        assert role.summary == summary

    def test_roles_collection(self):
        """Test Roles collection."""
        role1 = Role(
            basics=RoleBasics(
                company="Company 1",
                start_date=datetime(2020, 1, 1),
                title="Engineer",
            ),
        )
        role2 = Role(
            basics=RoleBasics(
                company="Company 2",
                start_date=datetime(2021, 1, 1),
                title="Senior Engineer",
            ),
        )
        roles = Roles(roles=[role1, role2])

        assert len(roles) == 2
        assert roles[0] == role1
        assert roles[1] == role2

    def test_project_creation(self):
        """Test Project model creation."""
        overview = ProjectOverview(
            title="Web App",
            start_date=datetime(2021, 1, 1),
            end_date=datetime(2021, 6, 1),
        )
        description = ProjectDescription(text="A web application")
        project = Project(overview=overview, description=description)
        assert project.overview == overview
        assert project.description == description

    def test_projects_collection(self):
        """Test Projects collection."""
        project1 = Project(
            overview=ProjectOverview(title="Project 1"),
            description=ProjectDescription(text="Description 1"),
        )
        project2 = Project(
            overview=ProjectOverview(title="Project 2"),
            description=ProjectDescription(text="Description 2"),
        )
        projects = Projects(projects=[project1, project2])

        assert len(projects) == 2
        assert projects[0] == project1
        assert projects[1] == project2

    def test_experience_creation(self):
        """Test Experience model creation."""
        roles = Roles(roles=[])
        projects = Projects(projects=[])
        experience = Experience(roles=roles, projects=projects)
        assert experience.roles == roles
        assert experience.projects == projects

    def test_role_basics_company_non_string(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleBasics(
                company=123,
                start_date=datetime.now(),
                title="Software Engineer",
            )

    def test_role_basics_company_empty(self):
        # missing test
        with pytest.raises(ValidationError, match="company must not be empty"):
            RoleBasics(
                company="  ",
                start_date=datetime.now(),
                title="Software Engineer",
            )

    def test_role_basics_title_non_string(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleBasics(company="Test", start_date=datetime.now(), title=123)

    def test_role_basics_title_empty(self):
        # missing test
        with pytest.raises(ValidationError, match="title must not be empty"):
            RoleBasics(company="Test", start_date=datetime.now(), title="  ")

    def test_role_basics_end_date_before_start(self):
        start = datetime(2022, 1, 1)
        end = datetime(2021, 1, 1)
        with pytest.raises(
            ValidationError,
            match="end_date must not be before start_date",
        ):
            RoleBasics(company="Test", title="Test", start_date=start, end_date=end)

    def test_role_basics_end_date_equal_to_start(self):
        """Test RoleBasics with end_date equal to start_date."""
        start_date = datetime(2022, 1, 1)
        basics = RoleBasics(
            company="Test",
            title="Test",
            start_date=start_date,
            end_date=start_date,
        )
        assert basics.end_date == start_date

    def test_role_basics_end_date_with_invalid_start_date(self):
        """Test end_date validation when start_date is invalid."""
        with pytest.raises(ValidationError) as excinfo:
            RoleBasics(
                company="Test",
                title="Test",
                start_date="not-a-date",
                end_date=datetime(2022, 1, 1),
            )
        errors = excinfo.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("start_date",)
        assert "Input should be a valid datetime" in errors[0]["msg"]

    def test_role_basics_end_date_is_none(self):
        """Test RoleBasics creation with end_date as None."""
        basics = RoleBasics(
            company="Test",
            title="Test",
            start_date=datetime.now(),
            end_date=None,
        )
        assert basics.end_date is None

    def test_role_basics_optional_string_non_string(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            RoleBasics(
                company="Test",
                title="Test",
                start_date=datetime.now(),
                location=123,
            )

    def test_roles_non_list(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Roles(roles="not a list")

    def test_roles_list_with_non_role(self):
        # missing test
        with pytest.raises(
            ValidationError,
            match="Input should be a valid dictionary or instance of Role",
        ):
            Roles(roles=["not a role"])

    def test_roles_iter(self):
        # missing test
        role1 = Role()
        roles_obj = Roles(roles=[role1])
        assert [r for r in roles_obj] == [role1]

    def test_roles_list_class(self):
        # missing test
        assert Roles().list_class == Role

    def test_project_skills_creation(self):
        """Test ProjectSkills model creation and validation."""
        skills_list = ["Django", "FastAPI"]
        project_skills = ProjectSkills(skills=skills_list)
        assert project_skills.skills == skills_list

    def test_project_skills_cleaning(self):
        """Test ProjectSkills cleans skills list."""
        skills_list = ["  Django ", "FastAPI", " ", ""]
        project_skills = ProjectSkills(skills=skills_list)
        assert project_skills.skills == ["Django", "FastAPI"]

    def test_project_skills_default_empty_list(self):
        """Test ProjectSkills defaults to an empty list."""
        project_skills = ProjectSkills()
        assert project_skills.skills == []

    def test_project_skills_iter(self):
        # missing test
        skills = ["a", "b"]
        ps = ProjectSkills(skills=skills)
        assert [s for s in ps] == skills

    def test_project_skills_len(self):
        # missing test
        skills = ["a", "b"]
        ps = ProjectSkills(skills=skills)
        assert len(ps) == 2

    def test_project_skills_getitem(self):
        # missing test
        skills = ["a", "b"]
        ps = ProjectSkills(skills=skills)
        assert ps[1] == "b"

    def test_project_overview_title_non_string(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            ProjectOverview(title=123)

    def test_project_overview_title_empty(self):
        # missing test
        with pytest.raises(ValidationError, match="title must not be empty"):
            ProjectOverview(title=" ")

    def test_project_overview_end_date_before_start(self):
        start = datetime(2022, 1, 1)
        end = datetime(2021, 1, 1)
        with pytest.raises(
            ValidationError,
            match="end_date must not be before start_date",
        ):
            ProjectOverview(title="Test", start_date=start, end_date=end)

    def test_project_overview_end_date_without_start_date(self):
        """Test ProjectOverview with an end_date but no start_date."""
        end_date = datetime(2022, 1, 1)
        overview = ProjectOverview(title="Test Project", end_date=end_date)
        assert overview.end_date == end_date
        assert overview.start_date is None

    def test_project_overview_end_date_equals_start_date(self):
        """Test ProjectOverview with end_date equal to start_date."""
        date = datetime(2022, 1, 1)
        overview = ProjectOverview(title="Test Project", start_date=date, end_date=date)
        assert overview.start_date == date
        assert overview.end_date == date

    def test_project_description_non_string(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            ProjectDescription(text=123)

    def test_projects_non_list(self):
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Projects(projects="not a list")

    def test_projects_list_with_non_project(self):
        # missing test
        with pytest.raises(
            ValidationError,
            match="Input should be a valid dictionary or instance of Project",
        ):
            Projects(projects=["not a project"])

    def test_projects_iter(self):
        # missing test
        proj1 = Project(
            overview=ProjectOverview(title="p1"),
            description=ProjectDescription(text="d1"),
        )
        projects_obj = Projects(projects=[proj1])
        assert [p for p in projects_obj] == [proj1]

    def test_projects_list_class(self):
        # missing test
        assert Projects().list_class == Project
