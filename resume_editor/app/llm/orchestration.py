import json
import logging
from typing import AsyncGenerator

from fastapi import Request
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI
from openai import AuthenticationError

from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    extract_education_info,
    extract_experience_info,
    extract_personal_info,
    serialize_certifications_to_markdown,
    serialize_education_to_markdown,
    serialize_experience_to_markdown,
    serialize_personal_info_to_markdown,
)
from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)
from resume_editor.app.llm.models import JobAnalysis, RefinedSection
from resume_editor.app.llm.prompts import (
    JOB_ANALYSIS_HUMAN_PROMPT,
    JOB_ANALYSIS_SYSTEM_PROMPT,
    RESUME_REFINE_HUMAN_PROMPT,
    RESUME_REFINE_SYSTEM_PROMPT,
    ROLE_REFINE_HUMAN_PROMPT,
    ROLE_REFINE_SYSTEM_PROMPT,
)
from resume_editor.app.models.resume.experience import Role

log = logging.getLogger(__name__)


def _get_section_content(resume_content: str, section_name: str) -> str:
    """
    Extracts the Markdown content for a specific section of the resume.

    Args:
        resume_content (str): The full resume content in Markdown.
        section_name (str): The name of the section to extract ("personal", "education", "experience", "certifications", or "full").

    Returns:
        str: The Markdown content of the specified section. Returns the full content if "full" is specified.

    Raises:
        ValueError: If the section_name is not one of the valid options.

    Notes:
        1. If section_name is "full", return the entire resume_content.
        2. Otherwise, map the section_name to a tuple of extractor and serializer functions.
        3. Validate that section_name is in the valid set of keys.
        4. Extract the data using the extractor function.
        5. Serialize the extracted data using the serializer function.
        6. Return the serialized result.

    """
    _msg = f"Extracting section '{section_name}' from resume"
    log.debug(_msg)

    if section_name == "full":
        return resume_content

    section_map = {
        "personal": (extract_personal_info, serialize_personal_info_to_markdown),
        "education": (extract_education_info, serialize_education_to_markdown),
        "experience": (extract_experience_info, serialize_experience_to_markdown),
        "certifications": (
            extract_certifications_info,
            serialize_certifications_to_markdown,
        ),
    }

    if section_name not in section_map:
        raise ValueError(f"Invalid section name: {section_name}")

    extractor, serializer = section_map[section_name]
    extracted_data = extractor(resume_content)
    return serializer(extracted_data)


async def analyze_job_description(
    job_description: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> JobAnalysis:
    """Uses an LLM to analyze a job description and extract key information.

    Args:
        job_description (str): The job description to analyze.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Returns:
        JobAnalysis: A pydantic object containing the structured analysis of the job description.

    Notes:
        1. Set up a PydanticOutputParser for structured output based on the JobAnalysis model.
        2. Create a PromptTemplate with instructions for the LLM.
        3. Determine the model name, using the provided `llm_model_name` or falling back to a default.
        4. Initialize the ChatOpenAI client.
        5. Create a chain combining the prompt, LLM, and parser.
        6. Asynchronously invoke the chain with the job description.
        7. Return the `JobAnalysis` object.

    Network access:
        - This function makes a network request to the LLM endpoint specified by llm_endpoint.
    """
    _msg = "analyze_job_description starting"
    log.debug(_msg)

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    parser = PydanticOutputParser(pydantic_object=JobAnalysis)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", JOB_ANALYSIS_SYSTEM_PROMPT),
            ("human", JOB_ANALYSIS_HUMAN_PROMPT),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    model_name = llm_model_name if llm_model_name else "gpt-4o"

    llm_params = {
        "model": model_name,
        "temperature": 0.7,
    }
    if llm_endpoint:
        llm_params["openai_api_base"] = llm_endpoint
        if "openrouter.ai" in llm_endpoint:
            llm_params["default_headers"] = {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            }

    if api_key:
        llm_params["api_key"] = api_key
    elif llm_endpoint and "openrouter.ai" not in llm_endpoint:
        llm_params["api_key"] = "not-needed"

    llm = ChatOpenAI(**llm_params)

    # Use StrOutputParser to get the raw string, then manually parse
    chain = prompt | llm | StrOutputParser()
    try:
        response_str = await chain.ainvoke({"job_description": job_description})

        parsed_json = parse_json_markdown(response_str)
        analysis = JobAnalysis.model_validate(parsed_json)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response as JSON: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again."
        ) from e

    _msg = "analyze_job_description returning"
    log.debug(_msg)
    return analysis


def _refine_generic_section(
    resume_content: str,
    job_description: str,
    target_section: str,
    llm: ChatOpenAI,
) -> str:
    """Uses a generic LLM chain to refine a non-experience section of the resume."""
    section_content = _get_section_content(resume_content, target_section)
    if not section_content.strip():
        _msg = f"Section '{target_section}' is empty, returning as-is."
        log.warning(_msg)
        return ""

    parser = PydanticOutputParser(pydantic_object=RefinedSection)

    goal_statement = "Rephrase and restructure the existing content from the `Resume Section to Refine` to be more impactful and relevant to the `Job Description`, while following all rules."

    processing_guidelines = ""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RESUME_REFINE_SYSTEM_PROMPT),
            ("human", RESUME_REFINE_HUMAN_PROMPT),
        ]
    ).partial(
        goal=goal_statement,
        processing_guidelines=processing_guidelines,
        format_instructions=parser.get_format_instructions(),
    )

    # Use StrOutputParser to get the raw string, then manually parse
    chain = prompt | llm | StrOutputParser()

    try:
        response_str = chain.invoke(
            {"job_description": job_description, "resume_section": section_content},
        )

        parsed_json = parse_json_markdown(response_str)
        refined_section = RefinedSection.model_validate(parsed_json)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response as JSON: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again."
        ) from e

    return refined_section.refined_markdown


def refine_resume_section_with_llm(
    resume_content: str,
    job_description: str,
    target_section: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> str:
    """
    Uses an LLM to refine a specific non-experience section of a resume based on a job description.

    This function acts as a dispatcher. For 'experience' section, it raises an error,
    directing the caller to use the appropriate async generator. For all other sections,
    it delegates to a generic helper function to perform a single-pass refinement.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        target_section (str): The section of the resume to refine (e.g., "personal").
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Returns:
        str: The refined Markdown content for the target section. Returns an empty string if the target section is empty.

    Raises:
        ValueError: If `target_section` is 'experience'.

    Network access:
        - This function makes network requests to the LLM endpoint specified by llm_endpoint.

    """
    _msg = f"refine_resume_section_with_llm starting for section '{target_section}'"
    log.debug(_msg)

    if target_section == "experience":
        # This section is handled by the async `refine_experience_section` generator
        # and should not be called with this synchronous function.
        raise ValueError(
            "Experience section refinement must be called via the async 'refine_experience_section' method."
        )
    else:
        model_name = llm_model_name if llm_model_name else "gpt-4o"

        llm_params = {
            "model": model_name,
            "temperature": 0.7,
        }
        if llm_endpoint:
            llm_params["openai_api_base"] = llm_endpoint
            if "openrouter.ai" in llm_endpoint:
                llm_params["default_headers"] = {
                    "HTTP-Referer": "http://localhost:8000/",
                    "X-Title": "Resume Editor",
                }

        if api_key:
            llm_params["api_key"] = api_key
        elif llm_endpoint and "openrouter.ai" not in llm_endpoint:
            # For non-OpenRouter custom endpoints (e.g. local LLMs), provide a
            # dummy key if none is given to satisfy the client library.
            llm_params["api_key"] = "not-needed"

        llm = ChatOpenAI(**llm_params)

        refined_content = _refine_generic_section(
            resume_content=resume_content,
            job_description=job_description,
            target_section=target_section,
            llm=llm,
        )

        _msg = "refine_resume_section_with_llm returning"
        log.debug(_msg)
        return refined_content


async def refine_role(
    role: Role,
    job_analysis: JobAnalysis,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> Role:
    """Uses an LLM to refine a single resume Role based on a job analysis.

    Args:
        role (Role): The structured Role object to refine.
        job_analysis (JobAnalysis): The structured job analysis to align with.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Returns:
        Role: The refined and validated Role object.

    Raises:
        ValueError: If the LLM response is not valid JSON or fails Pydantic validation.

    Notes:
        1. Set up a PydanticOutputParser for structured output based on the Role model.
        2. Serialize the input role and job_analysis objects to JSON strings.
        3. Create a PromptTemplate with instructions for the LLM.
        4. Determine the model name, using the provided `llm_model_name` or falling back to a default.
        5. Initialize the ChatOpenAI client.
        6. Create a chain combining the prompt, LLM, and a string output parser.
        7. Asynchronously invoke the chain with the serialized JSON data.
        8. Parse the LLM's string response to extract the JSON.
        9. Validate the extracted JSON against the Role model.
        10. Return the validated Role object.

    Network access:
        - This function makes a network request to the LLM endpoint.
    """
    _msg = "refine_role starting"
    log.debug(_msg)

    parser = PydanticOutputParser(pydantic_object=Role)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ROLE_REFINE_SYSTEM_PROMPT),
            ("human", ROLE_REFINE_HUMAN_PROMPT),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    model_name = llm_model_name if llm_model_name else "gpt-4o"

    llm_params = {
        "model": model_name,
        "temperature": 0.7,
    }
    if llm_endpoint:
        llm_params["openai_api_base"] = llm_endpoint
        if "openrouter.ai" in llm_endpoint:
            llm_params["default_headers"] = {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            }

    if api_key:
        llm_params["api_key"] = api_key
    elif llm_endpoint and "openrouter.ai" not in llm_endpoint:
        llm_params["api_key"] = "not-needed"

    llm = ChatOpenAI(**llm_params)

    chain = prompt | llm | StrOutputParser()

    # Serialize the Pydantic objects to JSON strings
    role_json = role.model_dump_json(indent=2)
    job_analysis_json = job_analysis.model_dump_json(indent=2)

    try:
        response_str = await chain.ainvoke(
            {
                "job_analysis_json": job_analysis_json,
                "role_json": role_json,
            },
        )
        parsed_json = parse_json_markdown(response_str)
        refined_role = Role.model_validate(parsed_json)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response for role refinement: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again."
        ) from e

    _msg = "refine_role returning"
    log.debug(_msg)
    return refined_role


async def _refine_experience_section(
    request: Request,
    resume_content: str,
    job_description: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> AsyncGenerator[dict[str, str], None]:
    # 1. Parse all sections of the resume
    yield {"status": "in_progress", "message": "Parsing resume..."}
    log.debug("Parsing resume...")
    personal_info = extract_personal_info(resume_content)
    education_info = extract_education_info(resume_content)
    certifications_info = extract_certifications_info(resume_content)
    experience_info = extract_experience_info(resume_content)

    # 2. Analyze the job description
    yield {"status": "in_progress", "message": "Analyzing job description..."}
    log.debug("Analyzing job description...")
    job_analysis = await analyze_job_description(
        job_description=job_description,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )

    # 3. Refine each role
    refined_roles: list[Role] = []
    client_disconnected = False
    if experience_info.roles:
        total_roles = len(experience_info.roles)
        for i, role in enumerate(experience_info.roles, 1):
            if await request.is_disconnected():
                _msg = "Client disconnected during experience refinement."
                log.warning(_msg)
                client_disconnected = True
                break
            status_msg = f"Refining role {i} of {total_roles}"
            yield {"status": "in_progress", "message": status_msg}
            log.debug(status_msg)
            refined_role = await refine_role(
                role=role,
                job_analysis=job_analysis,
                llm_endpoint=llm_endpoint,
                api_key=api_key,
                llm_model_name=llm_model_name,
            )
            refined_roles.append(refined_role)

    if client_disconnected:
        return

    # 4. Create new experience response with refined roles and original projects
    refined_experience = ExperienceResponse(
        roles=refined_roles, projects=experience_info.projects
    )

    # 5. Reconstruct the full resume
    yield {"status": "in_progress", "message": "Reconstructing resume..."}
    log.debug("Reconstructing resume...")
    updated_resume_content = reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education_info,
        certifications=certifications_info,
        experience=refined_experience,
    )

    yield {"status": "done", "content": updated_resume_content}


async def refine_experience_section(
    request: Request,
    resume_content: str,
    job_description: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> AsyncGenerator[dict[str, str], None]:
    """
    Orchestrates the asynchronous refinement of the 'experience' section of a resume.

    This function performs a multi-step process:
    1. Parses the entire resume to get structured data for all sections.
    2. Analyzes the job description to extract keywords, skills, and themes.
    3. Refines each professional role from the experience section individually.
    4. Reconstructs the full resume Markdown with the refined roles.

    It yields status updates as it progresses through these stages.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Yields:
        dict[str, str]: A dictionary containing the status of the operation
                        (e.g., "Parsing resume...", "Refining role 1 of 2").
                        The final event will have a status of "done" and include
                        the "content" of the fully refined resume.

    Raises:
        ValueError: If an unexpected error occurs during the process.
        AuthenticationError: If the LLM call fails due to an auth issue.
    """
    try:
        async for event in _refine_experience_section(
            request=request,
            resume_content=resume_content,
            job_description=job_description,
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        ):
            yield event

    except AuthenticationError as e:
        detail = "LLM authentication failed. Please check your API key in settings."
        _msg = f"LLM authentication error during experience refinement: {e!s}"
        log.warning(_msg)
        yield {"status": "error", "message": detail}
    except Exception as e:
        _msg = f"An unexpected error occurred during experience refinement: {e!s}"
        log.exception(_msg)
        yield {"status": "error", "message": str(e)}


