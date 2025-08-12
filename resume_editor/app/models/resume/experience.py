import logging
from datetime import datetime

from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


class RoleSummary(BaseModel):
    """Represents a brief description of a professional role.

    Attributes:
        summary (str): The text content of the role summary.

    """

    summary: str

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v):
        """Validate the summary field.

        Args:
            v: The summary value to validate. Must be a string.

        Returns:
            str: The validated summary.

        Notes:
            1. Ensure summary is a string.
            2. Raise a ValueError if summary is not a string.

        """
        if not isinstance(v, str):
            raise ValueError("summary must be a string")
        return v


class RoleResponsibilities(BaseModel):
    """Represents detailed descriptions of role responsibilities.

    Attributes:
        text (str): The text content of the responsibilities.

    """

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate the text field.

        Args:
            v: The text value to validate. Must be a string.

        Returns:
            str: The validated text.

        Notes:
            1. Ensure text is a string.
            2. Raise a ValueError if text is not a string.

        """
        if not isinstance(v, str):
            raise ValueError("text must be a string")
        return v


class RoleSkills(BaseModel):
    """Represents skills used in a professional role.

    Attributes:
        skills (List[str]): A list of non-empty, stripped skill strings.

    """

    skills: list[str] = []

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        """Validate the skills field.

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
        if not isinstance(v, list):
            raise ValueError("skills must be a list")
        cleaned_skills = []
        for skill in v:
            if not isinstance(skill, str):
                raise ValueError("all skills must be strings")
            stripped_skill = skill.strip()
            if stripped_skill:  # Only add non-empty skills
                cleaned_skills.append(stripped_skill)
        return cleaned_skills

    def __iter__(self):
        """Iterate over the skills.

        Returns:
            Iterator over the skills list.

        """
        return iter(self.skills)

    def __len__(self):
        """Return the number of skills.

        Returns:
            int: The number of skills.

        """
        return len(self.skills)

    def __getitem__(self, index):
        """Return the skill at the given index.

        Args:
            index (int): The index of the skill to return.

        Returns:
            str: The skill at the specified index.

        """
        return self.skills[index]


class RoleBasics(BaseModel):
    """Represents basic information about a professional role.

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

    @field_validator("company")
    @classmethod
    def validate_company(cls, v):
        """Validate the company field.

        Args:
            v: The company value to validate. Must be a non-empty string.

        Returns:
            str: The validated company.

        Notes:
            1. Ensure company is a string.
            2. Ensure company is not empty.
            3. Strip whitespace from the company name.
            4. Raise a ValueError if company is not a string or is empty.

        """
        if not isinstance(v, str):
            raise ValueError("company must be a string")
        if not v.strip():
            raise ValueError("company must not be empty")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate the title field.

        Args:
            v: The title value to validate. Must be a non-empty string.

        Returns:
            str: The validated title.

        Notes:
            1. Ensure title is a string.
            2. Ensure title is not empty.
            3. Strip whitespace from the title.
            4. Raise a ValueError if title is not a string or is empty.

        """
        if not isinstance(v, str):
            raise ValueError("title must be a string")
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v):
        """Validate the start_date field.

        Args:
            v: The start_date value to validate. Must be a datetime object.

        Returns:
            datetime: The validated start_date.

        Notes:
            1. Ensure start_date is a datetime object.
            2. Raise a ValueError if start_date is not a datetime object.

        """
        if not isinstance(v, datetime):
            raise ValueError("start_date must be a datetime object")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v, info):
        """Validate the end_date field.

        Args:
            v: The end_date value to validate. Must be a datetime object or None.
            info: Validation info containing data.

        Returns:
            datetime: The validated end_date.

        Notes:
            1. Ensure end_date is a datetime object or None.
            2. If end_date is provided, ensure it is not before start_date.
            3. Raise a ValueError if end_date is not a datetime object or None, or if end_date is before start_date.

        """
        if v is not None:
            if not isinstance(v, datetime):
                raise ValueError("end_date must be a datetime object or None")
            start_date = info.data.get("start_date")
            if start_date and v < start_date:
                raise ValueError("end_date must not be before start_date")
        return v

    @field_validator(
        "reason_for_change",
        "location",
        "job_category",
        "employment_type",
        "agency_name",
    )
    @classmethod
    def validate_optional_string_fields(cls, v):
        """Validate optional string fields.

        Args:
            v: The field value to validate. Must be a string or None.

        Returns:
            str: The validated field value.

        Notes:
            1. Ensure field is a string or None.
            2. Raise a ValueError if field is neither a string nor None.

        """
        if v is not None and not isinstance(v, str):
            raise ValueError("field must be a string or None")
        return v


class Role(BaseModel):
    """Represents a complete professional role with all associated details.

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
    """Represents a collection of professional roles.

    Attributes:
        roles (List[Role]): A list of Role objects.

    """

    roles: list[Role] = []

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v):
        """Validate the roles field.

        Args:
            v: The roles value to validate. Must be a list of Role objects.

        Returns:
            list[Role]: The validated roles list.

        Notes:
            1. Ensure roles is a list.
            2. Ensure all items in roles are Role objects.
            3. Raise a ValueError if roles is not a list or if any item is not a Role object.
            4. Return the validated list of roles.

        """
        if not isinstance(v, list):
            raise ValueError("roles must be a list")
        for item in v:
            if not isinstance(item, Role):
                raise ValueError("all items in roles must be Role instances")
        return v

    def __iter__(self):
        """Iterate over the roles.

        Returns:
            Iterator over the roles list.

        """
        return iter(self.roles)

    def __len__(self):
        """Return the number of roles.

        Returns:
            int: The number of roles.

        """
        return len(self.roles)

    def __getitem__(self, index):
        """Return the role at the given index.

        Args:
            index (int): The index of the role to return.

        Returns:
            Role: The role at the specified index.

        """
        return self.roles[index]

    @property
    def list_class(self):
        """Return the class for the list.

        Returns:
            The Role class.

        """
        return Role


class ProjectSkills(BaseModel):
    """Represents skills used in a project.

    Attributes:
        skills (List[str]): A list of non-empty, stripped skill strings.

    """

    skills: list[str] = []

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v):
        """Validate the skills field.

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
        if not isinstance(v, list):
            raise ValueError("skills must be a list")
        cleaned_skills = []
        for skill in v:
            if not isinstance(skill, str):
                raise ValueError("all skills must be strings")
            stripped_skill = skill.strip()
            if stripped_skill:  # Only add non-empty skills
                cleaned_skills.append(stripped_skill)
        return cleaned_skills

    def __iter__(self):
        """Iterate over the skills.

        Returns:
            Iterator over the skills list.

        """
        return iter(self.skills)

    def __len__(self):
        """Return the number of skills.

        Returns:
            int: The number of skills.

        """
        return len(self.skills)

    def __getitem__(self, index):
        """Return the skill at the given index.

        Args:
            index (int): The index of the skill to return.

        Returns:
            str: The skill at the specified index.

        """
        return self.skills[index]


class ProjectOverview(BaseModel):
    """Represents basic details of a project.

    Attributes:
        title (str): The title of the project.
        url (str | None): The URL for the project or None.
        url_description (str | None): A description of the URL or None.
        start_date (datetime | None): The start date as a datetime object or None.
        end_date (datetime | None): The end date as a datetime object or None.

    """

    title: str
    url: str | None = None
    url_description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate the title field.

        Args:
            v: The title value to validate. Must be a non-empty string.

        Returns:
            str: The validated title.

        Notes:
            1. Ensure title is a string.
            2. Ensure title is not empty.
            3. Strip whitespace from the title.
            4. Raise a ValueError if title is not a string or is empty.

        """
        if not isinstance(v, str):
            raise ValueError("title must be a string")
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("url", "url_description")
    @classmethod
    def validate_optional_strings(cls, v):
        """Validate optional string fields.

        Args:
            v: The field value to validate. Must be a string or None.

        Returns:
            str: The validated field value.

        Notes:
            1. Ensure field is a string or None.
            2. Raise a ValueError if field is neither a string nor None.

        """
        if v is not None and not isinstance(v, str):
            raise ValueError("field must be a string or None")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_dates(cls, v):
        """Validate the date fields.

        Args:
            v: The date value to validate. Must be a datetime object or None.

        Returns:
            datetime: The validated date.

        Notes:
            1. Ensure date is a datetime object or None.
            2. Raise a ValueError if date is not a datetime object or None.

        """
        if v is not None and not isinstance(v, datetime):
            raise ValueError("date must be a datetime object or None")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v, info):
        """Validate that start_date is not after end_date.

        Args:
            v: The end_date value to validate.
            info: Validation info containing data.

        Returns:
            datetime: The validated end_date.

        Notes:
            1. If both start_date and end_date are provided, ensure start_date is not after end_date.
            2. Raise a ValueError if end_date is before start_date.

        """
        if v is not None:
            start_date = info.data.get("start_date")
            if start_date is not None and v < start_date:
                raise ValueError("end_date must not be before start_date")
        return v


class ProjectDescription(BaseModel):
    """Represents a brief description of a project.

    Attributes:
        text (str): The text content of the project description.

    """

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate the text field.

        Args:
            v: The text value to validate. Must be a string.

        Returns:
            str: The validated text.

        Notes:
            1. Ensure text is a string.
            2. Raise a ValueError if text is not a string.

        """
        if not isinstance(v, str):
            raise ValueError("text must be a string")
        return v


class Project(BaseModel):
    """Represents a complete project with all associated details.

    Attributes:
        overview (ProjectOverview): The ProjectOverview object containing project metadata.
        description (ProjectDescription): The ProjectDescription object describing the project.
        skills (ProjectSkills | None): The ProjectSkills object listing skills used.

    """

    overview: ProjectOverview
    description: ProjectDescription
    skills: ProjectSkills | None = None


class Projects(BaseModel):
    """Represents a collection of projects.

    Attributes:
        projects (List[Project]): A list of Project objects.

    """

    projects: list[Project] = []

    @field_validator("projects")
    @classmethod
    def validate_projects(cls, v):
        """Validate the projects field.

        Args:
            v: The projects value to validate. Must be a list of Project objects.

        Returns:
            list[Project]: The validated projects list.

        Notes:
            1. Ensure projects is a list.
            2. Ensure all items in projects are Project objects.
            3. Raise a ValueError if projects is not a list or if any item is not a Project object.
            4. Return the validated list of projects.

        """
        if not isinstance(v, list):
            raise ValueError("projects must be a list")
        for item in v:
            if not isinstance(item, Project):
                raise ValueError("all items in projects must be Project instances")
        return v

    def __iter__(self):
        """Iterate over the projects.

        Returns:
            Iterator over the projects list.

        """
        return iter(self.projects)

    def __len__(self):
        """Return the number of projects.

        Returns:
            int: The number of projects.

        """
        return len(self.projects)

    def __getitem__(self, index):
        """Return the project at the given index.

        Args:
            index (int): The index of the project to return.

        Returns:
            Project: The project at the specified index.

        """
        return self.projects[index]

    @property
    def list_class(self):
        """Return the class of the list.

        Returns:
            The Project class.

        """
        return Project


class Experience(BaseModel):
    """Represents a collection of professional experience including roles and projects.

    Attributes:
        roles (Roles | None): A Roles object containing work experience.
        projects (Projects | None): A Projects object containing project details.

    """

    roles: Roles | None = None
    projects: Projects | None = None
