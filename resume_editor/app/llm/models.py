import logging

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class RefinedSection(BaseModel):
    """
    Pydantic model for the structured output from the LLM after refining a resume section.

    Attributes:
        refined_markdown (str): The refined resume section, formatted as a valid Markdown string.

    """

    refined_markdown: str = Field(
        ...,
        description="The refined resume section, formatted as a valid Markdown string.",
    )


class JobAnalysis(BaseModel):
    """A structured analysis of a job description, extracting key information."""

    required_skills: list[str] = Field(
        ..., description="A list of required skills from the job description."
    )
    nice_to_have_skills: list[str] = Field(
        ..., description="A list of nice-to-have skills from the job description."
    )
    job_title: str = Field(..., description="The job title from the job description.")
