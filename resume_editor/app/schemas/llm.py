import logging

from pydantic import BaseModel, Field

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
