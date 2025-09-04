import json
import logging

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI

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


def analyze_job_description(
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
        6. Invoke the chain with the job description.
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
        "temperature": 0.0,
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
        response_str = chain.invoke({"job_description": job_description})

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


def refine_resume_section_with_llm(
    resume_content: str,
    job_description: str,
    target_section: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> str:
    """
    Uses an LLM to refine a specific section of a resume based on a job description.

    Args:
        resume_content (str): The full Markdown content of the resume.
        job_description (str): The job description to align the resume with.
        target_section (str): The section of the resume to refine (e.g., "experience").
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Returns:
        str: The refined Markdown content for the target section. Returns an empty string if the target section is empty.

    Notes:
        1. Extract the target section content from the resume using _get_section_content.
        2. If the extracted content is empty, return an empty string.
        3. Set up a PydanticOutputParser for structured output based on the RefinedSection model.
        4. Create a PromptTemplate with instructions for the LLM, including format instructions.
        5. Determine the model name, using the provided `llm_model_name` or falling back to a default.
        6. Initialize the ChatOpenAI client. If a custom `llm_endpoint` is set without an `api_key`, a dummy API key is provided to satisfy the OpenAI client library.
        7. Create a chain combining the prompt, LLM, and parser.
        8. Invoke the chain with the job description and resume section content to get a `RefinedSection` object.
        9. Return the `refined_markdown` field from the result.

    Network access:
        - This function makes a network request to the LLM endpoint specified by llm_endpoint.

    """
    _msg = f"refine_resume_section_with_llm starting for section '{target_section}'"
    log.debug(_msg)

    section_content = _get_section_content(resume_content, target_section)
    if not section_content.strip():
        _msg = f"Section '{target_section}' is empty, returning as-is."
        log.warning(_msg)
        return ""

    parser = PydanticOutputParser(pydantic_object=RefinedSection)

    goal_statement = "Rephrase and restructure the existing content from the `Resume Section to Refine` to be more impactful and relevant to the `Job Description`, while following all rules."

    processing_guidelines = ""
    if target_section == "experience":
        processing_guidelines = """**Processing Guidelines:**

        Your goal is to make the resume as relevant as possible to the `Job Description` by refining its content. For each `### Role`:

        1.  **Rewrite Summaries:** Rewrite the `#### Summary` to focus on accomplishments and experiences that directly match the requirements in the `Job Description`.

        2.  **Update Responsibilities and Skills (Crucial):**
            - **Align Responsibilities:** Rewrite `#### Responsibilities` bullet points to use keywords and phrasing from the `Job Description`.
            - **Add Responsibility for Relevant Skills:** If a skill from the original `#### Skills` section is relevant to the `Job Description`, add a new bullet point to `#### Responsibilities` describing its use. For example: `* Used Splunk for monitoring and alerting.`
            - **Synchronize Skills:** After rewriting `#### Responsibilities`, review it. For **every** skill, technology, or method mentioned in the `Responsibilities` bullet points, ensure it is listed in the `#### Skills` section. The `Skills` section must be a superset of the skills mentioned in `Responsibilities`.
            - **Keep All Relevant Skills:** The `#### Skills` section should also include any other skills from the original resume that are relevant to the `Job Description`, even if they aren't used in a bullet point.

        3.  **Handle Non-Relevant Roles:** If a `### Role` has no experience or skills relevant to the `Job Description`, replace the content of its `#### Summary` and `#### Responsibilities` sections. The `#### Responsibilities` section should contain only a single bullet point: `* Duties not relevant to this job application.` The `#### Summary` should be empty. This is important to preserve the candidate's employment history."""

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

    _msg = "refine_resume_section_with_llm returning"
    log.debug(_msg)
    return refined_section.refined_markdown


def refine_role(
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
        7. Invoke the chain with the serialized JSON data.
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
        response_str = chain.invoke(
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


def refine_experience_section(
    resume_content: str,
    job_description: str,
    llm_endpoint: str | None,
    api_key: str | None,
    llm_model_name: str | None,
) -> str:
    """Orchestrates the multi-pass refinement of the experience section.

    Args:
        resume_content (str): The full resume content in Markdown.
        job_description (str): The job description to align the resume with.
        llm_endpoint (str | None): The custom LLM endpoint URL.
        api_key (str | None): The user's decrypted LLM API key.
        llm_model_name (str | None): The user-specified LLM model name.

    Returns:
        str: The complete, updated resume Markdown.

    Notes:
        1. Parse the full resume into structured data for all sections.
        2. Call `analyze_job_description` to get a structured analysis of the job.
        3. Iterate through each role from the parsed experience section.
        4. For each role, call `refine_role` with the role and job analysis to get a refined role.
        5. Collect the refined roles.
        6. Create a new `ExperienceResponse` object containing the refined roles and original projects.
        7. Call `reconstruct_resume_markdown` with the original parsed sections and the new refined experience section.
        8. Return the complete, updated resume Markdown.
    """
    _msg = "refine_experience_section starting"
    log.debug(_msg)

    # 1. Parse all sections of the resume
    personal_info = extract_personal_info(resume_content)
    education_info = extract_education_info(resume_content)
    certifications_info = extract_certifications_info(resume_content)
    experience_info = extract_experience_info(resume_content)

    # 2. Analyze the job description
    job_analysis = analyze_job_description(
        job_description=job_description,
        llm_endpoint=llm_endpoint,
        api_key=api_key,
        llm_model_name=llm_model_name,
    )

    # 3. Refine each role
    refined_roles: list[Role] = []
    for role in experience_info.roles:
        refined_role = refine_role(
            role=role,
            job_analysis=job_analysis,
            llm_endpoint=llm_endpoint,
            api_key=api_key,
            llm_model_name=llm_model_name,
        )
        refined_roles.append(refined_role)

    # 4. Create new experience response with refined roles
    refined_experience = ExperienceResponse(
        roles=refined_roles, projects=experience_info.projects
    )

    # 5. Reconstruct the full resume
    updated_resume_content = reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education_info,
        certifications=certifications_info,
        experience=refined_experience,
    )

    _msg = "refine_experience_section returning"
    log.debug(_msg)
    return updated_resume_content
