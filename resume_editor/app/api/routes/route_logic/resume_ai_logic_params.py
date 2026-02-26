"""Parameter dataclasses for resume AI logic."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessExperienceResultParams:
    """Parameters for processing refined experience results.

    Attributes:
        resume_id: ID of the resume being processed.
        original_resume_content: Original resume content before refinement.
        resume_content_to_refine: Content that underwent refinement.
        refined_roles: Dictionary of refined role data by index.
        job_description: The job description used for refinement.
        limit_refinement_years: Optional year limit for filtering.

    """

    resume_id: int
    original_resume_content: str
    resume_content_to_refine: str
    refined_roles: dict
    job_description: str
    limit_refinement_years: int | None
