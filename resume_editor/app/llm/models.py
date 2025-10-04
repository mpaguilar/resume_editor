import logging

from pydantic import BaseModel, Field

from resume_editor.app.models.resume.experience import (
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)

log = logging.getLogger(__name__)


class RefinedSection(BaseModel):
    """
    Pydantic model for the structured output from the LLM after refining a resume section.

    Attributes:
        refined_markdown (str): The refined resume section, formatted as a valid Markdown string.
        introduction (str | None): An optional AI-generated introductory paragraph for the resume.

    """

    refined_markdown: str = Field(
        ...,
        description="The refined resume section, formatted as a valid Markdown string.",
    )
    introduction: str | None = None


class JobAnalysis(BaseModel):
    """A structured analysis of a job description, extracting key information."""

    key_skills: list[str] = Field(
        ...,
        description="A list of the most important technical skills, soft skills, tools, and qualifications from the job description.",
    )
    primary_duties: list[str] = Field(
        ..., description="A list of the primary duties and responsibilities of the role."
    )
    themes: list[str] = Field(
        ...,
        description="A list of high-level themes, company culture points, or recurring keywords (e.g., 'fast-paced environment,' 'data-driven decisions').",
    )


class RefinedRole(BaseModel):
    """A structured representation of a single professional role, refined by an LLM."""

    basics: RoleBasics
    summary: RoleSummary | None = None
    responsibilities: RoleResponsibilities | None = None
    skills: RoleSkills | None = None
