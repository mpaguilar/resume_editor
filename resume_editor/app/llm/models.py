import logging

from pydantic import BaseModel, Field

from resume_editor.app.models.resume.experience import (
    Role,
    RoleBasics,
    RoleResponsibilities,
    RoleSkills,
    RoleSummary,
)

log = logging.getLogger(__name__)


class RefinedSection(BaseModel):
    """Pydantic model for the structured output from the LLM after refining a resume section.

    Attributes:
        refined_markdown (str): The refined resume section, formatted as a valid Markdown string.

    """

    refined_markdown: str = Field(
        ...,
        description="The refined resume section, formatted as a valid Markdown string.",
    )


class JobAnalysis(BaseModel):
    """A structured analysis of a job description, extracting key information."""

    key_skills: list[str] = Field(
        ...,
        description="A list of the most important technical skills, soft skills, tools, and qualifications from the job description.",
    )
    primary_duties: list[str] = Field(
        ...,
        description="A list of the primary duties and responsibilities of the role.",
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


class LLMConfig(BaseModel):
    """Configuration for LLM client initialization."""

    llm_endpoint: str | None = None
    api_key: str | None = None
    llm_model_name: str | None = None


class RoleRefinementJob(BaseModel):
    """Payload for a single role refinement task."""

    role: Role
    job_analysis: JobAnalysis
    llm_config: LLMConfig
    original_index: int


class JobKeyRequirements(BaseModel):
    """A structured analysis of a job description, extracting key information."""

    key_skills: list[str] = Field(
        ...,
        description="A list of the most critical skills and qualifications.",
    )
    candidate_priorities: list[str] = Field(
        ...,
        description="A bulleted list of what the hiring manager is looking for, with each point starting with a present-tense verb.",
    )


class SkillAssessment(BaseModel):
    """A qualitative assessment of a candidate's skill, including its source."""

    assessment: str = Field(
        ...,
        description="A qualitative assessment of the candidate's experience level (e.g., 'extensive experience', 'familiarity with').",
    )
    source: list[str] = Field(
        ...,
        description="A list of sources where this skill is demonstrated (e.g., ['Work Experience', 'Certification', 'Project']). Ordered by importance.",
    )


class CandidateAnalysis(BaseModel):
    """An analysis of the resume against job requirements."""

    skill_summary: dict[str, SkillAssessment] = Field(
        ...,
        description="A mapping of key skills from the job to a qualitative assessment and source of the candidate's experience.",
    )


class GeneratedIntroduction(BaseModel):
    """The final synthesized introduction."""

    introduction: str = Field(
        ...,
        description="A compelling, concise introductory paragraph.",
    )
