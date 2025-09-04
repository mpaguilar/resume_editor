import logging

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI

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
from resume_editor.app.schemas.llm import RefinedSection

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

    system_template = """As an expert resume writer, your task is to refine the following resume section to better align with the provided job description.

        **Crucial Rules:**
        1.  **Stick to the Facts:** You MUST NOT invent, embellish, or add any information that is not present in the original "Resume Section to Refine". Do not use superlatives or grandiose claims. All refined content must be directly traceable to the original text.
        2.  **Strictly Adhere to Format:** Your response MUST strictly follow the provided Markdown resume specification. Pay close attention to header levels (`#`, `##`, `###`, `####`), key-value pairs (`Key: Value`), and list formats.
        3.  **Skills Section Formatting:** The `Skills` section under a `Role` or `Project` MUST be a bulleted list. Each skill must be a separate line starting with `* `.

        **Goal:**
        {goal}

        {processing_guidelines}

        **Output Format:**
        Your response MUST be a single JSON object enclosed in ```json ... ```. The JSON object must conform to the following schema.

        {format_instructions}

        ---
        MARKDOWN RESUME SPECIFICATION EXAMPLE:
        # Personal
        ## Contact Information
        Name: Jane Doe

        # Experience
        ## Roles
        ### Role
        #### Basics
        Company: A Company, LLC
        Title: Engineer
        Start date: 01/2020
        #### Skills
        * Skill one
        * Skill two
        ---
    """

    human_template = """Job Description:
        {job_description}

        Resume Section to Refine:
        ---
        {resume_section}
        ---
        Now, output the JSON object:
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("human", human_template),
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

    return refined_section.refined_markdown
