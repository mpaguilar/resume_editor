"""Job analysis functions for LLM orchestration."""

import json
import logging

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI

from resume_editor.app.llm.models import JobAnalysis
from resume_editor.app.llm.orchestration_client import initialize_llm_client
from resume_editor.app.llm.prompts import (
    JOB_ANALYSIS_HUMAN_PROMPT,
    JOB_ANALYSIS_SYSTEM_PROMPT,
)

log = logging.getLogger(__name__)


def _parse_job_analysis_response(response_str: str) -> JobAnalysis:
    """Parse and validate job analysis LLM response.

    Args:
        response_str: The raw response string from the LLM.

    Returns:
        Validated JobAnalysis object.

    Raises:
        ValueError: If parsing or validation fails.

    Notes:
        1. Parses the response string as JSON.
        2. Validates the parsed JSON against the JobAnalysis model.

    """
    _msg = "_parse_job_analysis_response starting"
    log.debug(_msg)

    try:
        parsed_json = parse_json_markdown(response_str)
        analysis = JobAnalysis.model_validate(parsed_json)
    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response as JSON: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again.",
        ) from e

    _msg = "_parse_job_analysis_response returning"
    log.debug(_msg)
    return analysis


async def analyze_job_description(
    job_description: str,
    llm_config: object,
    resume_content_for_context: str,
) -> tuple[JobAnalysis, str | None]:
    """Uses an LLM to analyze a job description.

    Args:
        job_description: The job description to analyze.
        llm_config: LLM configuration including endpoint, API key, and model name.
        resume_content_for_context: The full resume content for context.

    Returns:
        Tuple of (JobAnalysis, introduction or None).

    Raises:
        ValueError: If job description is empty or parsing fails.

    Notes:
        1. Validates job description is not empty.
        2. Sets up PydanticOutputParser for structured output.
        3. Creates ChatPromptTemplate with system and human prompts.
        4. Initializes LLM client and creates invocation chain.
        5. Invokes chain asynchronously with job description.
        6. Parses and validates the response.

    Network access:
        - Makes a network request to the LLM endpoint.

    """
    _msg = "analyze_job_description starting"
    log.debug(_msg)

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    parser = PydanticOutputParser(pydantic_object=JobAnalysis)

    resume_content_block = (
        f"Resume Content:\n---\n{resume_content_for_context}\n---\n\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", JOB_ANALYSIS_SYSTEM_PROMPT),
            ("human", JOB_ANALYSIS_HUMAN_PROMPT),
        ],
    ).partial(format_instructions=parser.get_format_instructions())

    llm = initialize_llm_client(llm_config)

    from langchain_core.output_parsers import StrOutputParser

    chain = prompt | llm | StrOutputParser()

    response_str = await chain.ainvoke(
        {
            "job_description": job_description,
            "resume_content_block": resume_content_block,
        },
    )

    analysis = _parse_job_analysis_response(response_str)

    _msg = "analyze_job_description returning"
    log.debug(_msg)
    return analysis, getattr(analysis, "introduction", None)
