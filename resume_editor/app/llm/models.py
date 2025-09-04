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
    """
    Pydantic model for structured output from analyzing a job description.

    Attributes:
        key_skills (list[str]): Key skills, technologies, and qualifications.
        responsibilities (list[str]): Key responsibilities and duties.
        themes (list[str]): High-level themes or cultural aspects.
    """

    key_skills: list[str] = Field(
        ...,
        description="A list of key skills, technologies, and qualifications mentioned in the job description.",
    )
    responsibilities: list[str] = Field(
        ..., description="A list of key responsibilities and duties."
    )
    themes: list[str] = Field(
        ...,
        description='A list of high-level themes or cultural aspects mentioned (e.g., "fast-paced environment", "strong collaboration").',
    )
