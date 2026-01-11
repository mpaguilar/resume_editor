import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI
from openai import AuthenticationError
from pydantic import ValidationError

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
)
from resume_editor.app.llm.models import (
    CandidateAnalysis,
    GeneratedIntroduction,
    JobAnalysis,
    JobKeyRequirements,
    LLMConfig,
    RefinedRole,
    RoleRefinementJob,
)
from resume_editor.app.llm.prompts import (
    INTRO_ANALYZE_JOB_HUMAN_PROMPT,
    INTRO_ANALYZE_JOB_SYSTEM_PROMPT,
    INTRO_ANALYZE_RESUME_HUMAN_PROMPT,
    INTRO_ANALYZE_RESUME_SYSTEM_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT,
    JOB_ANALYSIS_HUMAN_PROMPT,
    JOB_ANALYSIS_SYSTEM_PROMPT,
    ROLE_REFINE_HUMAN_PROMPT,
    ROLE_REFINE_SYSTEM_PROMPT,
)
from resume_editor.app.models.resume.experience import Role

log = logging.getLogger(__name__)


DEFAULT_LLM_TEMPERATURE = 0.2


def _initialize_llm_client(llm_config: LLMConfig) -> ChatOpenAI:
    """Initializes the ChatOpenAI client from configuration.

    Args:
        llm_config (LLMConfig): Configuration for the LLM client.

    Returns:
        ChatOpenAI: An initialized ChatOpenAI client instance.

    Notes:
        1.  Determines the model name, using the provided `llm_model_name` or falling back to a default.
        2.  Sets up LLM parameters for temperature, endpoint, and headers (if OpenRouter is used).
        3.  Sets the API key if provided, or uses a dummy key if a custom endpoint is specified without a key.
        4.  Returns an initialized `ChatOpenAI` client.

    """
    model_name = llm_config.llm_model_name if llm_config.llm_model_name else "gpt-4o"
    llm_params: dict[str, Any] = {
        "model": model_name,
        "temperature": DEFAULT_LLM_TEMPERATURE,
    }
    if llm_config.llm_endpoint:
        llm_params["openai_api_base"] = llm_config.llm_endpoint
        if "openrouter.ai" in llm_config.llm_endpoint:
            llm_params["default_headers"] = {
                "HTTP-Referer": "http://localhost:8000/",
                "X-Title": "Resume Editor",
            }
    if llm_config.api_key:
        llm_params["api_key"] = llm_config.api_key
    elif llm_config.llm_endpoint and "openrouter.ai" not in llm_config.llm_endpoint:
        llm_params["api_key"] = "not-needed"

    return ChatOpenAI(**llm_params)


async def analyze_job_description(
    job_description: str,
    llm_config: LLMConfig,
    resume_content_for_context: str,
) -> tuple[JobAnalysis, str | None]:
    """Uses an LLM to analyze a job description.

    Args:
        job_description (str): The job description to analyze.
        llm_config (LLMConfig): LLM configuration including endpoint, API key, and model name.
        resume_content_for_context (str): The full resume content, used to provide context for the analysis.

    Returns:
        JobAnalysis: The structured analysis of the job description.

    Notes:
        1. Set up a `PydanticOutputParser` for structured output based on the `JobAnalysis` model.
        2. Prepare prompt components for with resume content for context.
        3. Create a `ChatPromptTemplate` with instructions for the LLM.
        4. Determine the model name, using the provided `llm_model_name` or falling back to a default.
        5. Initialize the `ChatOpenAI` client.
        6. Create a chain combining the prompt, LLM, and a `StrOutputParser`.
        7. Asynchronously invoke the chain with the job description and resume content.
        8. Parse the JSON response and validate it against the `JobAnalysis` model.
        9. Return the `JobAnalysis` object.

    Network access:
        - This function makes a network request to the LLM endpoint specified by llm_endpoint.

    """
    _msg = "analyze_job_description starting"
    log.debug(_msg)

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    parser = PydanticOutputParser(pydantic_object=JobAnalysis)

    # Conditionally prepare prompt components for introduction generation
    resume_content_block = (
        f"Resume Content:\n---\n{resume_content_for_context}\n---\n\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", JOB_ANALYSIS_SYSTEM_PROMPT),
            ("human", JOB_ANALYSIS_HUMAN_PROMPT),
        ],
    ).partial(
        format_instructions=parser.get_format_instructions(),
    )

    llm = _initialize_llm_client(llm_config)

    # Use StrOutputParser to get the raw string, then manually parse
    chain = prompt | llm | StrOutputParser()
    try:
        response_str = await chain.ainvoke(
            {
                "job_description": job_description,
                "resume_content_block": resume_content_block,
            },
        )

        parsed_json = parse_json_markdown(response_str)
        analysis = JobAnalysis.model_validate(parsed_json)

    except (json.JSONDecodeError, ValueError) as e:
        _msg = f"Failed to parse LLM response as JSON: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again.",
        ) from e

    _msg = "analyze_job_description returning"
    log.debug(_msg)
    return analysis, getattr(analysis, "introduction", None)


async def _refine_role_and_put_on_queue(
    job: RoleRefinementJob,
    semaphore: asyncio.Semaphore,
    event_queue: asyncio.Queue,
) -> None:
    """Refines a single role and puts progress/result events onto an asyncio.Queue.

    This function acts as a concurrent worker. It acquires a semaphore to limit
    concurrency, sends an 'in_progress' event to the queue, calls the `refine_role`
    LLM function, and then puts either the successful `role_refined` event or an
    exception onto the queue.

    Args:
        job (RoleRefinementJob): The refinement job containing the role, job analysis, LLM configuration, and original index.
        semaphore (asyncio.Semaphore): The semaphore to control concurrency.
        event_queue (asyncio.Queue): The queue to send events to.

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
        log.debug(
            "Waiting on semaphore for role refinement for index %d",
            job.original_index,
        )
        async with semaphore:
            role_title = f"{job.role.basics.title} @ {job.role.basics.company}"
            await event_queue.put(
                {
                    "status": "in_progress",
                    "message": f"Refining role '{role_title}'...",
                },
            )

            log.debug(
                "Semaphore acquired, refining role for index %d",
                job.original_index,
            )
            refined_role = await refine_role(
                role=job.role,
                job_analysis=job.job_analysis,
                llm_config=job.llm_config,
            )
            await event_queue.put(
                {
                    "status": "role_refined",
                    "data": refined_role.model_dump(mode="json"),
                    "original_index": job.original_index,
                },
            )
    except Exception as e:
        await event_queue.put(e)


async def async_refine_experience_section(
    resume_content: str,
    job_description: str,
    llm_config: LLMConfig,
    max_concurrency: int = 5,
) -> AsyncGenerator[dict[str, Any], None]:
    """Orchestrates the CONCURRENT refinement of the 'experience' section of a resume.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        llm_config (LLMConfig): LLM configuration including endpoint, API key, and model name.
        max_concurrency (int): The maximum number of roles to refine in parallel.

    Yields:
        dict[str, Any]: Status updates and refined role data.

    Notes:
        1. Yields progress messages for parsing the resume and analyzing the job description.
        2. Extracts experience information from the resume. If no roles are found, the function returns.
        3. Analyzes the job description to get key requirements, yielding a `job_analysis_complete` event.
        4. Generates an AI introduction based on the job analysis, yielding an `in_progress` status event, and then an `introduction_generated` status event with the introduction text.
        5. Creates an `asyncio.Queue` for events and a `Semaphore` to limit concurrency.
        6. For each role, a background task is created to perform refinement and put events on the queue.
        7. Enters a loop to consume events from the queue, yielding them until all roles are processed.
        8. After the event loop, `asyncio.gather` is called to ensure all background tasks have completed.

    """
    log.debug("async_refine_experience_section starting")

    # 1. Parse the experience section of the resume
    yield {"status": "in_progress", "message": "Parsing resume..."}
    log.debug("Parsing resume...")
    experience_info = extract_experience_info(resume_content)

    # 2. Analyze the job description
    yield {"status": "in_progress", "message": "Analyzing job description..."}
    log.debug("Analyzing job description...")

    job_analysis, _ = await analyze_job_description(
        job_description=job_description,
        llm_config=llm_config,
        resume_content_for_context=resume_content,
    )
    yield {"status": "job_analysis_complete", "message": "Job analysis complete."}

    llm = _initialize_llm_client(llm_config)

    yield {"status": "in_progress", "message": "Generating AI introduction..."}
    try:
        generated_intro_text = _generate_introduction_from_analysis(
            job_analysis_json=job_analysis.model_dump_json(),
            resume_content=resume_content,
            llm=llm,
        )
        if generated_intro_text:
            yield {
                "status": "introduction_generated",
                "data": generated_intro_text,
            }
    except Exception:
        log.exception("Failed to generate introduction during experience refinement.")

    # 3. Create and dispatch tasks for role refinement
    num_roles = len(experience_info.roles) if experience_info.roles else 0
    if num_roles == 0:
        log.warning("No roles found in experience section to refine.")
        return

    event_queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(max_concurrency)

    tasks = []
    for index, role in enumerate(experience_info.roles):
        job = RoleRefinementJob(
            role=role,
            job_analysis=job_analysis,
            llm_config=llm_config,
            original_index=index,
        )
        task = asyncio.create_task(
            _refine_role_and_put_on_queue(
                job=job,
                semaphore=semaphore,
                event_queue=event_queue,
            ),
        )
        tasks.append(task)

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

    await asyncio.gather(*tasks, return_exceptions=True)
    log.debug("async_refine_experience_section finishing")


async def refine_role(
    role: Role,
    job_analysis: JobAnalysis,
    llm_config: LLMConfig,
) -> RefinedRole:
    """Uses an LLM to refine a single resume Role based on a job analysis.

    Args:
        role (Role): The structured Role object to refine.
        job_analysis (JobAnalysis): The structured job analysis to align with.
        llm_config (LLMConfig): LLM configuration including endpoint, API key, and model name.

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
        ],
    ).partial(format_instructions=parser.get_format_instructions())

    llm = _initialize_llm_client(llm_config)

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

    except AuthenticationError:
        raise
    except Exception as e:
        _msg = f"An unexpected error occurred during role refinement: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again.",
        ) from e

    # Preserve the original inclusion status, as the AI should not decide this.
    refined_role.basics.inclusion_status = role.basics.inclusion_status

    _msg = "refine_role returning"
    log.debug(_msg)
    return refined_role


def _invoke_chain_and_parse(chain: Any, pydantic_model: Any, **kwargs: Any) -> Any:
    """Invokes a LangChain chain, gets content, parses JSON, and validates with Pydantic.

    Args:
        chain (Any): The LangChain runnable chain to invoke.
        pydantic_model (Any): The Pydantic model to validate the parsed JSON against.
        **kwargs (Any): Keyword arguments to pass to the chain's invoke method.

    Returns:
        Any: An instance of the `pydantic_model` populated with the parsed data.

    Raises:
        json.JSONDecodeError: If the LLM's response content is not valid JSON.
        ValidationError: If the parsed JSON does not conform to the `pydantic_model`.

    Notes:
        1. Invokes the provided LangChain `chain` with the given `kwargs`.
        2. Extracts the content string from the result.
        3. Parses the content string as JSON using `parse_json_markdown`.
        4. Validates the parsed JSON against the `pydantic_model`.
        5. Returns the validated Pydantic model instance.
        6. No network, disk, or database access is performed.

    """
    _msg = "_invoke_chain_and_parse starting"
    log.debug(_msg)

    result = chain.invoke(kwargs)
    result_str = result.content
    parsed_json = parse_json_markdown(result_str)
    validated_model = pydantic_model.model_validate(parsed_json)

    _msg = "_invoke_chain_and_parse returning"
    log.debug(_msg)
    return validated_model


def _generate_introduction_from_analysis(
    job_analysis_json: str,
    resume_content: str,
    llm: ChatOpenAI,
) -> str:
    """Orchestrates the resume analysis and introduction synthesis steps.

    Args:
        job_analysis_json (str): A JSON string representing the pre-analyzed job requirements,
                                 conforming to the `JobKeyRequirements` model.
        resume_content (str): The full Markdown content of the resume.
        llm (ChatOpenAI): An initialized ChatOpenAI client instance.

    Returns:
        str: The generated introduction as a Markdown-formatted bulleted list,
             or an empty string if generation fails.

    Notes:
        1.  **Step 1: Resume Analysis**: Creates a chain with `INTRO_ANALYZE_RESUME_PROMPT` and a parser for `CandidateAnalysis`.
            It invokes this chain with the `resume_content` and the `job_analysis_json`.
        2.  **Step 2: Introduction Synthesis**: Creates a chain with `INTRO_SYNTHESIZE_INTRODUCTION_PROMPT` and a parser for `GeneratedIntroduction`.
            It invokes this chain with the JSON output from the resume analysis step.
        3.  Extracts the `strengths` list from the final Pydantic object and formats it as a Markdown bulleted list.
        4.  Handles JSON decoding and Pydantic validation errors by logging and returning an empty string.
        5.  This function performs multiple network requests to the configured LLM endpoint.

    """
    _msg = "_generate_introduction_from_analysis starting"
    log.debug(_msg)

    try:
        # Step 2 from original: Resume Analysis
        resume_analysis_parser = PydanticOutputParser(pydantic_object=CandidateAnalysis)
        resume_analysis_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTRO_ANALYZE_RESUME_SYSTEM_PROMPT),
                ("human", INTRO_ANALYZE_RESUME_HUMAN_PROMPT),
            ],
        ).partial(format_instructions=resume_analysis_parser.get_format_instructions())
        resume_analysis_chain = resume_analysis_prompt | llm
        candidate_analysis = _invoke_chain_and_parse(
            resume_analysis_chain,
            CandidateAnalysis,
            resume_content=resume_content,
            job_requirements=job_analysis_json,
        )

        # Step 3 from original: Synthesis
        synthesis_parser = PydanticOutputParser(pydantic_object=GeneratedIntroduction)
        synthesis_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT),
                ("human", INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT),
            ],
        ).partial(format_instructions=synthesis_parser.get_format_instructions())
        synthesis_chain = synthesis_prompt | llm
        generated_introduction = _invoke_chain_and_parse(
            synthesis_chain,
            GeneratedIntroduction,
            candidate_analysis=candidate_analysis.model_dump_json(),
        )

        strengths = generated_introduction.strengths
        introduction = "\n".join(f"- {s}" for s in strengths)

    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        _msg = f"Failed during introduction generation chain: {e!s}"
        log.exception(_msg)
        introduction = ""

    _msg = "_generate_introduction_from_analysis returning"
    log.debug(_msg)
    return introduction


def generate_introduction_from_resume(
    resume_content: str,
    job_description: str,
    llm_config: LLMConfig,
) -> str:
    """Generates a resume introduction using a multi-step LLM chain.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the introduction with.
        llm_config (LLMConfig): Configuration for the LLM client.

    Returns:
        str: The generated introduction, or an empty string if generation fails.

    Notes:
        1.  Initializes a ChatOpenAI client using the provided `llm_config`.
        2.  **Step 1: Job Analysis**: Creates a chain with `INTRO_ANALYZE_JOB_PROMPT` to extract key skills and priorities from the job description.
        3.  Calls `_generate_introduction_from_analysis` with the job analysis result to perform the subsequent resume analysis and synthesis steps.
        4.  Handles exceptions during the job analysis step and returns an empty string on failure.
        5.  This function performs multiple network requests to the configured LLM endpoint.

    """
    _msg = "generate_introduction_from_resume starting"
    log.debug(_msg)

    # Initialize LLM client
    llm = _initialize_llm_client(llm_config)

    try:
        # Step 1: Job Analysis
        job_analysis_parser = PydanticOutputParser(pydantic_object=JobKeyRequirements)
        job_analysis_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTRO_ANALYZE_JOB_SYSTEM_PROMPT),
                ("human", INTRO_ANALYZE_JOB_HUMAN_PROMPT),
            ],
        ).partial(format_instructions=job_analysis_parser.get_format_instructions())
        job_analysis_chain = job_analysis_prompt | llm
        job_analysis = _invoke_chain_and_parse(
            job_analysis_chain,
            JobKeyRequirements,
            job_description=job_description,
        )

    except (json.JSONDecodeError, ValidationError, ValueError) as e:
        _msg = f"Failed during introduction generation (Job Analysis step): {e!s}"
        log.exception(_msg)
        return ""

    introduction = _generate_introduction_from_analysis(
        job_analysis_json=job_analysis.model_dump_json(),
        resume_content=resume_content,
        llm=llm,
    )

    _msg = "generate_introduction_from_resume returning"
    log.debug(_msg)
    return introduction
