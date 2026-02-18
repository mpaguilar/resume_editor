import logging
from typing import Literal

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


class FactualEvidence(BaseModel):
    """A single piece of factual evidence extracted from the resume, with its source."""

    evidence: str = Field(
        ...,
        description="A direct quote or a concise summary of a fact from the resume that supports a job requirement.",
    )
    source_section: str = Field(
        ...,
        description="The resume section where the evidence was found (e.g., 'Work Experience', 'Education', 'Project', 'Certification', 'Personal').",
    )
    relevance: Literal["direct", "indirect"] | None = Field(
        None,
        description="For 'Work Experience' evidence, indicates if it's 'direct' or 'indirect' to the role's primary duties.",
    )


class CandidateRequirementAnalysis(BaseModel):
    """Links a single job requirement to factual evidence from the resume."""

    job_requirement: str = Field(
        ...,
        description="A single key skill or priority from the job description.",
    )
    evidence: list[FactualEvidence] = Field(
        default_factory=list,
        description="A list of factual statements from the resume supporting this requirement. If no evidence is found, this should be an empty list.",
    )


class CandidateAnalysis(BaseModel):
    """An analysis of the resume against job requirements, backed by factual evidence."""

    analysis: list[CandidateRequirementAnalysis] = Field(
        ...,
        description="A list aligning each job requirement to factual evidence from the resume.",
    )


class GeneratedIntroduction(BaseModel):
    """The final synthesized introduction."""

    strengths: list[str] = Field(
        ...,
        description="A bulleted list of the candidate's key strengths and qualifications, tailored to the job.",
    )
