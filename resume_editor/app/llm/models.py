import logging
from datetime import datetime
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
    inferred_themes: list[str] = Field(
        default_factory=list,
        description="Implicit themes inferred from job description language, tone, and subtext (e.g., 'leadership potential,' 'collaborative culture').",
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


class RefinedRoleRecord(BaseModel):
    """A record tracking a single refined role for the checkpoint system.

    This model captures the refined data for a single professional role,
    including the description, skills, and metadata about when it was refined.
    Used as part of the RunningLog to enable failure recovery and resume
    refinement from where it left off.

    Args:
        original_index: The position of this role in the original resume.
        company: The company name for this role.
        title: The job title for this role.
        refined_description: The refined description/summary of the role.
        relevant_skills: List of relevant skills identified during refinement.
        start_date: The start date of the role.
        end_date: The end date of the role (None if current position).
        timestamp: When this role was refined.

    """

    original_index: int = Field(
        ...,
        description="The position of this role in the original resume.",
    )
    company: str = Field(
        ...,
        description="The company name for this role.",
    )
    title: str = Field(
        ...,
        description="The job title for this role.",
    )
    refined_description: str = Field(
        ...,
        description="The refined description/summary of the role.",
    )
    relevant_skills: list[str] = Field(
        default_factory=list,
        description="List of relevant skills identified during refinement.",
    )
    start_date: datetime = Field(
        ...,
        description="The start date of the role.",
    )
    end_date: datetime | None = Field(
        None,
        description="The end date of the role (None if current position).",
    )
    timestamp: datetime = Field(
        ...,
        description="When this role was refined.",
    )


class RunningLog(BaseModel):
    """A container for tracking an entire refinement session.

    This model maintains the state of a resume refinement session,
    including the job description, cached job analysis, and all
    refined roles. It enables failure recovery by allowing refinement
    to resume from where it left off if an error occurs.

    Args:
        resume_id: The ID of the resume being refined.
        user_id: The ID of the user performing the refinement.
        job_description: The job description text being targeted.
        job_analysis: Cached job analysis (None until analyzed).
        refined_roles: List of successfully refined roles.
        created_at: When this log was created.
        updated_at: When this log was last updated.

    """

    resume_id: int = Field(
        ...,
        description="The ID of the resume being refined.",
    )
    user_id: int = Field(
        ...,
        description="The ID of the user performing the refinement.",
    )
    job_description: str = Field(
        ...,
        description="The job description text being targeted.",
    )
    job_analysis: JobAnalysis | None = Field(
        None,
        description="Cached job analysis (None until analyzed).",
    )
    refined_roles: list[RefinedRoleRecord] = Field(
        default_factory=list,
        description="List of successfully refined roles.",
    )
    created_at: datetime = Field(
        ...,
        description="When this log was created.",
    )
    updated_at: datetime = Field(
        ...,
        description="When this log was last updated.",
    )


class CrossSectionEvidence(BaseModel):
    """Evidence extracted from non-experience sections (Education, Certifications, Projects).

    This model captures relevant facts from sections of the resume outside
    of work experience that support the candidate's qualifications for a job.

    Args:
        section_type: The type of section (Education, Certification, Project).
        content: The factual content extracted from the section.
        relevance_score: How relevant this evidence is to the job (1-10).

    """

    section_type: str = Field(
        ...,
        description="The type of section: 'Education', 'Certification', or 'Project'.",
    )
    content: str = Field(
        ...,
        description="The factual content or achievement extracted from the section.",
    )
    relevance_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Relevance score from 1-10 indicating how well this supports job requirements.",
    )


class BannerBullet(BaseModel):
    """A single bullet point for the resume banner/introduction.

    Each bullet represents a category of skills or experience with
    a bold prefix and supporting description with company associations.

    Args:
        category: The bold prefix category (e.g., 'Leadership', 'Cloud Platforms').
        description: The descriptive text with skills and parenthetical companies.

    """

    category: str = Field(
        ...,
        description="The bold prefix category that semantically groups this bullet (e.g., 'Leadership', 'Cloud Platforms').",
    )
    description: str = Field(
        ...,
        description="The descriptive text listing skills with parenthetical company associations where applicable.",
    )


class GeneratedBanner(BaseModel):
    """The complete generated banner with multiple bullet points.

    This model contains the structured banner content generated from
    the running log data, organized into semantically coherent bullets.

    Args:
        bullets: List of BannerBullet objects representing the banner content.
        education_bullet: Optional bullet for education if highly relevant.

    """

    bullets: list[BannerBullet] = Field(
        default_factory=list,
        description="List of bullet points for the banner, ordered by relevance to the job.",
    )
    education_bullet: BannerBullet | None = Field(
        None,
        description="Optional education bullet, only included if directly relevant to job requirements.",
    )
