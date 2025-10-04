import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from fastapi import Request
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI
from openai import AuthenticationError

from resume_editor.app.api.routes.html_fragments import _create_refine_result_html
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
from resume_editor.app.llm.models import JobAnalysis, RefinedRole, RefinedSection
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
    generate_introduction: bool,
) -> tuple[str, str | None]:
    """Uses a generic LLM chain to refine a non-experience section of the resume.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        target_section (str): The section of the resume to refine.
        llm (ChatOpenAI): An initialized ChatOpenAI client instance.
        generate_introduction (bool): Whether to request an introduction.

    Returns:
        tuple[str, str | None]: A tuple containing the refined Markdown content
             for the target section and an optional introduction. Returns an empty
             string and None if the target section is empty.

    Raises:
        ValueError: If the LLM response is not valid JSON or fails Pydantic validation.

    Notes:
        1. Extracts the target section content from the resume using `_get_section_content`.
        2. If the extracted content is empty, returns an empty string and None.
        3. Sets up a `PydanticOutputParser` for structured output based on the `RefinedSection` model.
        4. Conditionally modifies the prompt's goal to request an introduction if `generate_introduction` is True.
        5. Creates a `ChatPromptTemplate` with instructions for the LLM.
        6. Creates a chain combining the prompt, LLM, and a `StrOutputParser`.
        7. Streams the response from the chain and joins the chunks.
        8. Parses the LLM's JSON-Markdown output using `parse_json_markdown`.
        9. Validates the parsed JSON against the `RefinedSection` model.
        10. Extracts the `refined_markdown` and optionally the `introduction` from the validated result.
        11. Returns a tuple of `(refined_markdown, introduction)`.
    """
    section_content = _get_section_content(resume_content, target_section)
    if not section_content.strip():
        _msg = f"Section '{target_section}' is empty, returning as-is."
        log.warning(_msg)
        return "", None

    parser = PydanticOutputParser(pydantic_object=RefinedSection)

    goal_statement = "Rephrase and restructure the existing content from the `Resume Section to Refine` to be more impactful and relevant to the `Job Description`, while following all rules."

    if generate_introduction:
        goal_statement += " Additionally, write a brief (1-2 paragraph) professional introduction for the resume based on the content and job description, and place it in the 'introduction' field of the JSON output."

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
        # Use streaming to avoid issues with some models returning non-JSON responses
        # with a JSON content-type header, which causes the OpenAI client to fail
        # on parsing.
        response_chunks = []
        for chunk in chain.stream(
            {"job_description": job_description, "resume_section": section_content},
        ):
            response_chunks.append(chunk)

        response_str = "".join(response_chunks)

        parsed_json = parse_json_markdown(response_str)
        refined_section = RefinedSection.model_validate(parsed_json)
        introduction = getattr(refined_section, "introduction", None)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response as JSON: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again."
        ) from e

    return refined_section.refined_markdown, introduction


async def _refine_role_and_put_on_queue(
    role: Role,
    job_analysis: JobAnalysis,
    semaphore: asyncio.Semaphore,
    event_queue: asyncio.Queue,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
    original_index: int,
) -> None:
    """
    Refines a single role and puts progress/result events onto an asyncio.Queue.

    This function acts as a concurrent worker. It acquires a semaphore to limit
    concurrency, sends an 'in_progress' event to the queue, calls the `refine_role`
    LLM function, and then puts either the successful `role_refined` event or an
    exception onto the queue.

    Args:
        role (Role): The structured role object to refine.
        job_analysis (JobAnalysis): The structured job analysis to use as context.
        semaphore (asyncio.Semaphore): The semaphore to control concurrency.
        event_queue (asyncio.Queue): The queue to send events to.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.
        original_index (int): The original index of the role in the resume.

    Returns:
        None

    Notes:
        1. This function is a coroutine.
        2. It waits to acquire the provided semaphore.
        3. Once acquired, it puts an 'in_progress' status message onto the `event_queue`.
        4. It calls `refine_role` to perform the actual LLM refinement.
        5. It puts the result of the refinement (a `role_refined` dictionary) onto the `event_queue`.
        6. If any exception occurs during the process, it puts the exception object onto the `event_queue`.
        7. The semaphore is released automatically by the `async with` block.
    """
    try:
        log.debug("Waiting on semaphore for role refinement for index %d", original_index)
        async with semaphore:
            role_title = f"{role.basics.title} @ {role.basics.company}"
            await event_queue.put(
                {
                    "status": "in_progress",
                    "message": f"Refining role '{role_title}'...",
                }
            )

            log.debug("Semaphore acquired, refining role for index %d", original_index)
            refined_role = await refine_role(
                role=role,
                job_analysis=job_analysis,
                llm_endpoint=llm_endpoint,
                api_key=api_key,
                llm_model_name=llm_model_name,
            )
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": original_index,
                }
            )
    except Exception as e:
        await event_queue.put(e)


async def async_refine_experience_section(
    resume_content: str,
    job_description: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
    generate_introduction: bool,
    max_concurrency: int = 5,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Orchestrates the CONCURRENT refinement of the 'experience' section of a resume.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.
        generate_introduction (bool): Whether to generate an introduction.
        max_concurrency (int): The maximum number of roles to refine in parallel.

    Yields:
        dict[str, Any]: Status updates and refined role data.

    Notes:
        1. Yields a progress message for parsing the resume.
        2. Extracts the experience section from the resume content.
        3. Yields a progress message for analyzing the job description.
        4. Calls `analyze_job_description` to get a structured analysis.
        5. If roles are found, creates an `asyncio.Queue` for events and a `Semaphore` for concurrency control.
        6. For each role, creates a concurrent task using `_refine_role_and_put_on_queue`.
        7. Enters a loop to consume events from the queue until all roles are processed.
        8. For each event, if it's an exception, it is raised. Otherwise, it is yielded to the caller.
    """
    log.debug("async_refine_experience_section starting")

    # 1. Parse the experience section of the resume
    yield {"status": "in_progress", "message": "Parsing resume..."}
    log.debug("Parsing resume...")
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

    # 3. Create and dispatch tasks for role refinement
    num_roles = len(experience_info.roles) if experience_info.roles else 0
    if num_roles == 0:
        log.warning("No roles found in experience section to refine.")
        return

    event_queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(max_concurrency)

    for index, role in enumerate(experience_info.roles):
        asyncio.create_task(
            _refine_role_and_put_on_queue(
                role=role,
                job_analysis=job_analysis,
                semaphore=semaphore,
                event_queue=event_queue,
                llm_endpoint=llm_endpoint,
                api_key=api_key,
                llm_model_name=llm_model_name,
                original_index=index,
            )
        )

    # 4. Yield events from the queue
    processed_count = 0
    while processed_count < num_roles:
        event = await event_queue.get()
        if isinstance(event, Exception):
            raise event

        if event.get("status") in ("role_refined",):
            processed_count += 1

        yield event
        event_queue.task_done()

    log.debug("async_refine_experience_section finishing")




def refine_resume_section_with_llm(
    resume_content: str,
    job_description: str,
    target_section: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
    generate_introduction: bool,
) -> tuple[str, str | None]:
    """Uses an LLM to refine a specific non-experience section of a resume.

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
        generate_introduction (bool): Whether to generate an introduction.

    Returns:
        tuple[str, str | None]: A tuple containing the refined Markdown content for
             the target section and an optional introduction. Returns an empty
             string and None if the target section is empty.

    Raises:
        ValueError: If `target_section` is 'experience'.

    Network access:
        - This function makes network requests to the LLM endpoint specified by
          llm_endpoint.

    Notes:
        1. Checks if `target_section` is 'experience' and raises a `ValueError` if so.
        2. Determines the model name, falling back to a default if not provided.
        3. Constructs parameters for `ChatOpenAI`, including the model name, endpoint,
           and API key. A dummy API key is used for custom, non-OpenRouter endpoints if
           no key is provided.
        4. Initializes the `ChatOpenAI` client.
        5. Calls `_refine_generic_section` with the resume content, job description,
           target section, and the initialized LLM client.
        6. Returns the tuple of refined content and introduction from the helper function.

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

        refined_content, introduction = _refine_generic_section(
            resume_content=resume_content,
            job_description=job_description,
            target_section=target_section,
            llm=llm,
            generate_introduction=generate_introduction,
        )

        _msg = "refine_resume_section_with_llm returning"
        log.debug(_msg)
        return refined_content, introduction


async def refine_role(
    role: Role,
    job_analysis: JobAnalysis,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> RefinedRole:
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
        10. Preserves the original `inclusion_status` of the role, as this is a user-controlled setting.
        11. Return the validated Role object.

    Network access:
        - This function makes a network request to the LLM endpoint.
    """
    _msg = "refine_role starting"
    log.debug(_msg)

    parser = PydanticOutputParser(pydantic_object=RefinedRole)

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
        refined_role = RefinedRole.model_validate(parsed_json)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response for role refinement: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again."
        ) from e

    # Preserve the original inclusion status, as the AI should not decide this.
    refined_role.basics.inclusion_status = role.basics.inclusion_status

    _msg = "refine_role returning"
    log.debug(_msg)
    return refined_role




