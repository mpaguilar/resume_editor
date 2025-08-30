import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


class InclusionStatus(str, Enum):
    """
    Represents the inclusion status of a resume item.

    Attributes:
        INCLUDE (str): Indicates the item should be included in the resume.
        NOT_RELEVANT (str): Indicates the item is not relevant to the resume.
        OMIT (str): Indicates the item should be omitted from the resume.
    """

    INCLUDE = "Include"
    NOT_RELEVANT = "Not Relevant"
    OMIT = "Omit"


class RoleSummary(BaseModel):
    """
    Represents a brief description of a professional role.

    Attributes:
        text (str): The text content of the role summary.
    """

    text: str


class RoleResponsibilities(BaseModel):
    """
    Represents detailed descriptions of role responsibilities.

    Attributes:
        text (str): The text content of the responsibilities.
    """

    text: str


class RoleSkills(BaseModel):
    """
    Represents skills used in a professional role.

    Attributes:
        skills (list[str]): A list of non-empty, stripped skill strings.
    """

    skills: list[str] = []

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        """
        Validate the skills field.

        Args:
            v: The skills value to validate. Must be a list of strings.

        Returns:
            list[str]: The validated and cleaned skills list.

        Notes:
            1. Ensure skills is a list.
            2. Ensure all items in skills are strings.
            3. Strip whitespace from each skill and filter out empty strings.
            4. Raise a ValueError if skills is not a list or if any skill is not a string.
            5. Return the cleaned list of non-empty skills.
        """
        cleaned_skills = []
        for skill in v:
            stripped_skill = skill.strip()
            if stripped_skill:
                cleaned_skills.append(stripped_skill)
        return cleaned_skills

    def __iter__(self):
        """
        Iterate over the skills.

        Returns:
            Iterator over the skills list.
        """
        return iter(self.skills)

    def __len__(self):
        """
        Return the number of skills.

        Returns:
            int: The number of skills.
        """
        return len(self.skills)

    def __getitem__(self, index):
        """
        Return the skill at the given index.

        Args:
            index (int): The index of the skill to return.

        Returns:
            str: The skill at the specified index.
        """
        return self.skills[index]


class RoleBasics(BaseModel):
    """
    Represents basic information about a professional role.

    Attributes:
        company (str): The name of the company.
        start_date (datetime): The start date of the role.
        end_date (datetime | None): The end date of the role or None if still ongoing.
        title (str): The job title.
        reason_for_change (str | None): The reason for leaving the role or None.
        location (str | None): The job location or None.
        job_category (str | None): The category of the job or None.
        employment_type (str | None): The employment type or None.
        agency_name (str | None): The name of the agency or None.
        inclusion_status (InclusionStatus): The inclusion status of the role.
    """

    company: str
    start_date: datetime
    end_date: datetime | None = None
    title: str
    reason_for_change: str | None = None
    location: str | None = None
    job_category: str | None = None
    employment_type: str | None = None
    agency_name: str | None = None
    inclusion_status: InclusionStatus = InclusionStatus.INCLUDE

    @field_validator("company")
    @classmethod
    def validate_company(cls, v):
        """
        Validate the company field.

        Args:
            v: The company value to validate. Must be a non-empty string.

        Returns:
            str: The validated company.

        Raises:
            ValueError: If company is not a string or is empty.

        Notes:
            1. Ensure company is a string.
            2. Ensure company is not empty.
            3. Strip whitespace from the company name.
            4. Raise a ValueError if company is not a string or is empty.
        """
        if not v.strip():
            raise ValueError("company must not be empty")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """
        Validate the title field.

        Args:
            v: The title value to validate. Must be a non-empty string.

        Returns:
            str: The validated title.

        Raises:
            ValueError: If title is not a string or is empty.

        Notes:
            1. Ensure title is a string.
            2. Ensure title is not empty.
            3. Strip whitespace from the title.
            4. Raise a ValueError if title is not a string or is empty.
        """
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        """
        Validate the end_date field.

        Args:
            v: The end_date value to validate. Must be a datetime object or None.
            info: Validation info containing data.

        Returns:
            datetime: The validated end_date.

        Raises:
            ValueError: If end_date is not a datetime object or None, or if end_date is before start_date.

        Notes:
            1. Ensure end_date is a datetime object or None.
            2. If end_date is provided, ensure it is not before start_date.
            3. Raise a ValueError if end_date is not a datetime object or None, or if end_date is before start_date.
        """
        if v is None:
            return v

        if "start_date" not in info.data:
            # start_date validation failed.
            return v

        start_date = info.data["start_date"]

        if v < start_date:
            raise ValueError("end_date must not be before start_date")

        return v


class Role(BaseModel):
    """
    Represents a complete professional role with all associated details.

    Attributes:
        basics (RoleBasics | None): The RoleBasics object containing role metadata.
        summary (RoleSummary | None): The RoleSummary object describing the role.
        responsibilities (RoleResponsibilities | None): The RoleResponsibilities object listing duties.
        skills (RoleSkills | None): The RoleSkills object listing skills used.
    """

    basics: RoleBasics | None = None
    summary: RoleSummary | None = None
    responsibilities: RoleResponsibilities | None = None
    skills: RoleSkills | None = None


class Roles(BaseModel):
    """
    Represents a collection of professional roles.

    Attributes:
        roles (list[Role]): A list of Role objects.
    """

    roles: list[Role] = []

    def __iter__(self):
        """
        Iterate over the roles.

        Returns:
            Iterator over the roles list.
        """
        return iter(self.roles)

    def __len__(self):
        """
        Return the number of roles.

        Returns:
            int: The number of roles.
        """
        return len(self.roles)

    def __getitem__(self, index):
        """
        Return the role at the given index.

        Args:
            index (int): The index of the role to return.

        Returns:
            Role: The role at the specified index.
        """
        return self.roles[index]

    @property
    def list_class(self):
        """
        Return the class for the list.

        Returns:
            The Role class.
        """
        return Role


class ProjectSkills(BaseModel):
    """
    Represents skills used in a project.

    Attributes:
        skills (list[str]): A list of non-empty, stripped skill strings.
    """

    skills: list[str] = []

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        """
        Validate the skills field.

        Args:
            v: The skills value to validate. Must be a list of strings.

        Returns:
            list[str]: The validated and cleaned skills list.

        Raises:
            ValueError: If skills is not a list or if any skill is not a string.

        Notes:
            1. Ensure skills is a list.
            2. Ensure all items in skills are strings.
            3. Strip whitespace from each skill and filter out empty strings.
            4. Raise a ValueError if skills is not a list or if any skill is not a string.
            5. Return the cleaned list of non-empty skills.
        """
        cleaned_skills = []
        for skill in v:
            stripped_skill = skill.strip()
            if stripped_skill:
                cleaned_skills.append(stripped_skill)
        return cleaned_skills

    def __iter__(self):
        """
        Iterate over the skills.

        Returns:
            Iterator over the skills list.
        """
        return iter(self.skills)

    def __len__(self):
        """
        Return the number of skills.

        Returns:
            int: The number of skills.
        """
        return len(self.skills)

    def __getitem__(self, index):
        """
        Return the skill at the given index.

        Args:
            index (int): The index of the skill to return.

        Returns:
            str: The skill at the specified index.
        """
        return self.skills[index]


class ProjectOverview(BaseModel):
    """
    Represents basic details of a project.

    Attributes:
        title (str): The title of the project.
        url (str | None): The URL for the project or None.
        url_description (str | None): A description of the URL or None.
        start_date (datetime | None): The start date as a datetime object or None.
        end_date (datetime | None): The end date as a datetime object or None.
        inclusion_status (InclusionStatus): The inclusion status of the project.
    """

    title: str
    url: str | None = None
    url_description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    inclusion_status: InclusionStatus = InclusionStatus.INCLUDE

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """
        Validate the title field.

        Args:
            v: The title value to validate. Must be a non-empty string.

        Returns:
            str: The validated title.

        Raises:
            ValueError: If title is not a string or is empty.

        Notes:
            1. Ensure title is a string.
            2. Ensure title is not empty.
            3. Strip whitespace from the title.
            4. Raise a ValueError if title is not a string or is empty.
        """
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v, info):
        """
        Validate that start_date is not after end_date.

        Args:
            v: The end_date value to validate.
            info: Validation info containing data.

        Returns:
            datetime: The validated end_date.

        Raises:
            ValueError: If end_date is before start_date.

        Notes:
            1. If both start_date and end_date are provided, ensure start_date is not after end_date.
            2. Raise a ValueError if end_date is before start_date.
        """
        if v is not None and (start_date := info.data.get("start_date")) is not None:
            if v < start_date:
                raise ValueError("end_date must not be before start_date")
        return v


class ProjectDescription(BaseModel):
    """
    Represents a brief description of a project.

    Attributes:
        text (str): The text content of the project description.
    """

    text: str


class Project(BaseModel):
    """
    Represents a complete project with all associated details.

    Attributes:
        overview (ProjectOverview | None): The ProjectOverview object containing project metadata.
        description (ProjectDescription): The ProjectDescription object describing the project.
        skills (ProjectSkills | None): The ProjectSkills object listing skills used.
    """

    overview: ProjectOverview | None = None
    description: ProjectDescription
    skills: ProjectSkills | None = None


class Projects(BaseModel):
    """
    Represents a collection of projects.

    Attributes:
        projects (list[Project]): A list of Project objects.
    """

    projects: list[Project] = []

    def __iter__(self):
        """
        Iterate over the projects.

        Returns:
            Iterator over the projects list.
        """
        return iter(self.projects)

    def __len__(self):
        """
        Return the number of projects.

        Returns:
            int: The number of projects.
        """
        return len(self.projects)

    def __getitem__(self, index):
        """
        Return the project at the given index.

        Args:
            index (int): The index of the project to return.

        Returns:
            Project: The project at the specified index.
        """
        return self.projects[index]

    @property
    def list_class(self):
        """
        Return the class of the list.

        Returns:
            The Project class.
        """
        return Project


class Experience(BaseModel):
    """
    Represents a collection of professional experience including roles and projects.

    Attributes:
        roles (Roles | None): A Roles object containing work experience.
        projects (Projects | None): A Projects object containing project details.
    """

    roles: Roles | None = None
    projects: Projects | None = None
