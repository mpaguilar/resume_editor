import logging

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
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
        6. Initialize the ChatOpenAI client with the determined model name, temperature, API base, and API key.
        7. Create a chain combining the prompt, LLM, and parser.
        8. Invoke the chain with the job description and resume section content.
        9. Parse the LLM's JSON-Markdown output using `parse_json_markdown` if the result is a string.
        10. Validate the parsed JSON against the `RefinedSection` model.
        11. Return the `refined_markdown` field from the validated result.

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

    prompt = PromptTemplate(
        template="""As an expert resume writer, refine the following resume section to better align with the provided job description.
        Your goal is to highlight the most relevant skills and experiences.
        Do not invent new facts. Rephrase and restructure the existing content to be more impactful.
        Return the result as a Markdown-formatted JSON object that follows the schema.

        {format_instructions}

        Job Description:
        {job_description}

        Resume Section to Refine:
        ---
        {resume_section}
        ---
        """,
        input_variables=["job_description", "resume_section"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    model_name = llm_model_name if llm_model_name else "gpt-4o"
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        openai_api_base=llm_endpoint,
        api_key=api_key,
    )

    chain = prompt | llm | parser

    result = chain.invoke(
        {"job_description": job_description, "resume_section": section_content},
    )

    # Note: langchain can return JSON in a markdown block, which needs parsing.
    # The Pydantic parser should handle this, but being explicit is safer.
    if isinstance(result, str):
        parsed_json = parse_json_markdown(result)
        refined_section = RefinedSection.model_validate(parsed_json)
    else:
        refined_section = result

    return refined_section.refined_markdown
