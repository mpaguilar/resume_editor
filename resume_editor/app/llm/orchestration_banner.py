"""Banner generation functions for LLM orchestration."""

import json
import logging
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langchain_openai import ChatOpenAI

from resume_editor.app.llm.models import (
    CrossSectionEvidence,
    GeneratedBanner,
    JobAnalysis,
    JobKeyRequirements,
    RefinedRoleRecord,
    RunningLog,
)
from resume_editor.app.llm.orchestration_client import initialize_llm_client
from resume_editor.app.llm.prompts import (
    BANNER_GENERATION_HUMAN_PROMPT,
    BANNER_GENERATION_SYSTEM_PROMPT,
    INTRO_ANALYZE_JOB_HUMAN_PROMPT,
    INTRO_ANALYZE_JOB_SYSTEM_PROMPT,
    INTRO_ANALYZE_RESUME_HUMAN_PROMPT,
    INTRO_ANALYZE_RESUME_SYSTEM_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT,
)

log = logging.getLogger(__name__)


def _is_section_header(line: str, section_header: str) -> bool:
    """Check if a line is the target section header.

    Args:
        line: The line to check.
        section_header: The expected section header (lowercase).

    Returns:
        True if line matches the section header.

    """
    stripped = line.strip().lower()
    return stripped.startswith(section_header) and not stripped.startswith("## ")


def _is_next_section(line: str) -> bool:
    """Check if a line is the start of a new section.

    Args:
        line: The line to check.

    Returns:
        True if line starts a new section.

    """
    stripped = line.strip().lower()
    return stripped.startswith("# ") and not stripped.startswith("## ")


def _find_section_start(lines: list[str], section_header: str) -> int:
    """Find the index where a section starts.

    Args:
        lines: All lines from the resume.
        section_header: The section header to look for.

    Returns:
        Index of first line after section header, or -1 if not found.

    """
    for i, line in enumerate(lines):
        if _is_section_header(line, section_header):
            return i + 1
    return -1


def _capture_section_content(lines: list[str], start_index: int) -> str:
    """Capture content from start index until next section.

    Args:
        lines: All lines from the resume.
        start_index: Index to start capturing from.

    Returns:
        Captured section content as string.

    """
    captured_lines = []
    for line in lines[start_index:]:
        if _is_next_section(line):
            break
        captured_lines.append(line)

    if captured_lines:
        return "\n".join(captured_lines).strip()
    return ""


def _extract_section_content(resume_content: str, section_name: str) -> str | None:
    """Extract the raw content of a section from resume markdown.

    Args:
        resume_content: The full Markdown content.
        section_name: The name of the section to extract.

    Returns:
        The section content or None if not found.

    Notes:
        1. Looks for a header matching # SectionName (case-insensitive).
        2. Captures content until the next # header or end of content.

    """
    lines = resume_content.splitlines()
    section_header = f"# {section_name.lower()}"

    start_index = _find_section_start(lines, section_header)
    if start_index < 0:
        return None

    result = _capture_section_content(lines, start_index)
    return result if result else None


def _has_skill_match(line_lower: str, job_skills_lower: list[str]) -> bool:
    """Check if line contains any job skill.

    Args:
        line_lower: Lowercase line to check.
        job_skills_lower: Lowercase job skills for matching.

    Returns:
        True if any skill matches.

    """
    return any(skill in line_lower for skill in job_skills_lower)


def _has_theme_match(line_lower: str, job_themes_lower: list[str]) -> bool:
    """Check if line contains any job theme.

    Args:
        line_lower: Lowercase line to check.
        job_themes_lower: Lowercase job themes for matching.

    Returns:
        True if any theme matches.

    """
    return any(theme in line_lower for theme in job_themes_lower)


def _is_advanced_degree(line_lower: str) -> bool:
    """Check if line indicates an advanced degree.

    Args:
        line_lower: Lowercase line to check.

    Returns:
        True if advanced degree detected.

    """
    return any(term in line_lower for term in ["master", "phd", "doctorate", "mba"])


def _has_senior_themes(job_themes_lower: list[str]) -> bool:
    """Check if themes indicate senior-level role.

    Args:
        job_themes_lower: Lowercase job themes.

    Returns:
        True if senior themes detected.

    """
    all_themes = " ".join(job_themes_lower)
    return any(
        term in all_themes for term in ["senior", "lead", "principal", "advanced"]
    )


def _calculate_education_relevance(
    education_line: str,
    job_skills_lower: list[str],
    job_themes_lower: list[str],
) -> int:
    """Calculate relevance score for an education entry.

    Args:
        education_line: A line from the education section.
        job_skills_lower: Lowercase job skills for matching.
        job_themes_lower: Lowercase job themes for matching.

    Returns:
        Relevance score from 1-10.

    Notes:
        1. Base score of 5 for any degree.
        2. +2 if field of study matches job skills/themes.
        3. +1 for advanced degrees with senior roles.

    """
    score = 5
    line_lower = education_line.lower()

    if _has_skill_match(line_lower, job_skills_lower):
        score += 2

    if _has_theme_match(line_lower, job_themes_lower):
        score += 1

    if _is_advanced_degree(line_lower) and _has_senior_themes(job_themes_lower):
        score += 1

    return min(score, 10)


def _calculate_certification_relevance(
    cert_line: str,
    job_skills_lower: list[str],
) -> int:
    """Calculate relevance score for a certification entry.

    Args:
        cert_line: A line from the certifications section.
        job_skills_lower: Lowercase job skills for matching.

    Returns:
        Relevance score from 1-10.

    Notes:
        1. Base score of 6 for any certification.
        2. +3 if certification matches a job skill.

    """
    score = 6
    line_lower = cert_line.lower()

    for skill in job_skills_lower:
        if skill in line_lower:
            score += 3
            break

    return min(score, 10)


def _calculate_project_relevance(
    project_chunk: str,
    job_skills_lower: list[str],
    job_themes_lower: list[str],
) -> int:
    """Calculate relevance score for a project entry.

    Args:
        project_chunk: Text describing a project.
        job_skills_lower: Lowercase job skills for matching.
        job_themes_lower: Lowercase job themes for matching.

    Returns:
        Relevance score from 1-10.

    Notes:
        1. Base score of 4 for any project.
        2. +2 for each matching job skill (up to +4).
        3. +1 for each matching theme (up to +2).

    """
    score = 4
    chunk_lower = project_chunk.lower()

    skill_matches = sum(1 for skill in job_skills_lower if skill in chunk_lower)
    score += min(skill_matches * 2, 4)

    theme_matches = sum(1 for theme in job_themes_lower if theme in chunk_lower)
    score += min(theme_matches, 2)

    return min(score, 10)


def _split_projects_section(projects_section: str) -> list[str]:
    """Split the projects section into individual project chunks.

    Args:
        projects_section: The content of the projects section.

    Returns:
        List of project chunks.

    """
    lines = projects_section.splitlines()
    chunks = []
    current_chunk = []

    for line in lines:
        if line.strip().startswith("### "):
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
        current_chunk.append(line)

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks if chunks else [projects_section]


def _extract_education_evidence(
    resume_content: str,
    job_analysis: JobAnalysis,
) -> list[CrossSectionEvidence]:
    """Extract education-related evidence.

    Args:
        resume_content: The resume markdown content.
        job_analysis: The job analysis for context.

    Returns:
        List of education evidence items.

    """
    evidence_list = []
    job_skills_lower = [skill.lower() for skill in job_analysis.key_skills]
    job_themes_lower = [
        theme.lower() for theme in job_analysis.themes + job_analysis.inferred_themes
    ]

    education_section = _extract_section_content(resume_content, "education")
    if not education_section:
        return evidence_list

    degree_keywords = [
        "bachelor",
        "master",
        "phd",
        "doctorate",
        "bs",
        "ms",
        "ba",
        "ma",
        "mba",
    ]

    for line in education_section.split("\n"):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in degree_keywords):
            relevance = _calculate_education_relevance(
                line, job_skills_lower, job_themes_lower
            )
            if relevance >= 5:
                evidence_list.append(
                    CrossSectionEvidence(
                        section_type="Education",
                        content=line.strip(),
                        relevance_score=relevance,
                    ),
                )

    return evidence_list


def _extract_certification_evidence(
    resume_content: str,
    job_analysis: JobAnalysis,
) -> list[CrossSectionEvidence]:
    """Extract certification-related evidence.

    Args:
        resume_content: The resume markdown content.
        job_analysis: The job analysis for context.

    Returns:
        List of certification evidence items.

    """
    evidence_list = []
    job_skills_lower = [skill.lower() for skill in job_analysis.key_skills]

    certifications_section = _extract_section_content(resume_content, "certifications")
    if not certifications_section:
        return evidence_list

    for line in certifications_section.split("\n"):
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith("#"):
            relevance = _calculate_certification_relevance(
                line_stripped, job_skills_lower
            )
            if relevance >= 6:
                evidence_list.append(
                    CrossSectionEvidence(
                        section_type="Certification",
                        content=line_stripped,
                        relevance_score=relevance,
                    ),
                )

    return evidence_list


def _extract_project_evidence(
    resume_content: str,
    job_analysis: JobAnalysis,
) -> list[CrossSectionEvidence]:
    """Extract project-related evidence.

    Args:
        resume_content: The resume markdown content.
        job_analysis: The job analysis for context.

    Returns:
        List of project evidence items.

    """
    evidence_list = []
    job_skills_lower = [skill.lower() for skill in job_analysis.key_skills]
    job_themes_lower = [
        theme.lower() for theme in job_analysis.themes + job_analysis.inferred_themes
    ]

    projects_section = _extract_section_content(resume_content, "projects")
    if not projects_section:
        return evidence_list

    project_chunks = _split_projects_section(projects_section)
    for chunk in project_chunks:
        relevance = _calculate_project_relevance(
            chunk, job_skills_lower, job_themes_lower
        )
        if relevance >= 5:
            evidence_list.append(
                CrossSectionEvidence(
                    section_type="Project",
                    content=chunk.strip()[:200],
                    relevance_score=relevance,
                ),
            )

    return evidence_list


def _extract_cross_section_evidence(
    resume_content: str,
    job_analysis: JobAnalysis,
) -> list[CrossSectionEvidence]:
    """Extract relevant evidence from Education, Certifications, and Projects.

    Args:
        resume_content: The full Markdown content.
        job_analysis: The job analysis containing key skills and themes.

    Returns:
        List of evidence items ordered by relevance score.

    """
    _msg = "_extract_cross_section_evidence starting"
    log.debug(_msg)

    evidence_list: list[CrossSectionEvidence] = []

    evidence_list.extend(_extract_education_evidence(resume_content, job_analysis))
    evidence_list.extend(_extract_certification_evidence(resume_content, job_analysis))
    evidence_list.extend(_extract_project_evidence(resume_content, job_analysis))

    evidence_list.sort(key=lambda x: x.relevance_score, reverse=True)

    _msg = f"_extract_cross_section_evidence returning {len(evidence_list)} items"
    log.debug(_msg)
    return evidence_list


def _format_role_data_for_banner(
    refined_roles: list[RefinedRoleRecord],
) -> list[dict[str, Any]]:
    """Format refined role records for banner generation input.

    Args:
        refined_roles: List of refined role records.

    Returns:
        Formatted role data suitable for LLM prompt.

    """
    _msg = "_format_role_data_for_banner starting"
    log.debug(_msg)

    formatted_roles = []
    for role in refined_roles:
        role_data = {
            "company": role.company,
            "title": role.title,
            "description": role.refined_description[:300]
            if len(role.refined_description) > 300
            else role.refined_description,
            "skills": role.relevant_skills,
            "position": role.original_index,
        }
        formatted_roles.append(role_data)

    formatted_roles.sort(key=lambda x: x["position"])

    _msg = f"_format_role_data_for_banner returning {len(formatted_roles)} roles"
    log.debug(_msg)
    return formatted_roles


def _invoke_banner_generation_chain(
    llm: ChatOpenAI,
    job_analysis: JobAnalysis,
    refined_roles: list[RefinedRoleRecord],
    cross_section_evidence: list[CrossSectionEvidence],
    original_banner: str | None,
) -> GeneratedBanner | None:
    """Invoke the LLM chain for banner generation.

    Args:
        llm: Initialized ChatOpenAI client.
        job_analysis: The job analysis for context.
        refined_roles: List of refined role records.
        cross_section_evidence: Cross-section evidence.
        original_banner: Original banner for context (optional).

    Returns:
        GeneratedBanner or None if generation fails.

    """
    _msg = "_invoke_banner_generation_chain starting"
    log.debug(_msg)

    try:
        parser = PydanticOutputParser(pydantic_object=GeneratedBanner)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", BANNER_GENERATION_SYSTEM_PROMPT),
                ("human", BANNER_GENERATION_HUMAN_PROMPT),
            ],
        ).partial(format_instructions=parser.get_format_instructions())

        from langchain_core.output_parsers import StrOutputParser

        chain = prompt | llm | StrOutputParser()

        formatted_roles = _format_role_data_for_banner(refined_roles)

        response_str = chain.invoke(
            {
                "job_analysis_json": job_analysis.model_dump_json(),
                "refined_roles_json": json.dumps(formatted_roles, indent=2),
                "cross_section_evidence_json": json.dumps(
                    [e.model_dump() for e in cross_section_evidence], indent=2
                ),
                "original_banner": original_banner or "",
            },
        )

        parsed_json = parse_json_markdown(response_str)
        banner = GeneratedBanner.model_validate(parsed_json)

        _msg = "_invoke_banner_generation_chain returning successfully"
        log.debug(_msg)
        return banner

    except Exception as e:
        _msg = f"Banner generation chain failed: {e!s}"
        log.exception(_msg)
        return None


def _parse_json_with_fix(json_string: str) -> Any:
    """Parse a JSON string, attempting to fix common LLM-produced errors.

    Args:
        json_string: The JSON string to parse.

    Returns:
        The parsed Python object.

    Raises:
        json.JSONDecodeError: If parsing fails after attempting fixes.

    """
    try:
        return parse_json_markdown(json_string)
    except json.JSONDecodeError as e:
        if "Invalid \\escape" in str(e):
            import re

            corrected_json_string = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", json_string)
            try:
                return parse_json_markdown(corrected_json_string)
            except json.JSONDecodeError:
                raise e
        else:
            raise e


def _invoke_chain_and_parse(
    chain: Any,
    pydantic_model: Any,
    **kwargs: Any,
) -> Any:
    """Invokes a chain, parses JSON, and validates with Pydantic.

    Args:
        chain: The LangChain runnable chain.
        pydantic_model: The Pydantic model for validation.
        **kwargs: Keyword arguments for chain invocation.

    Returns:
        Validated Pydantic model instance.

    Raises:
        ValueError: If parsing or validation fails.

    """
    _msg = "_invoke_chain_and_parse starting"
    log.debug(_msg)

    try:
        result = chain.invoke(kwargs)
        result_str = result.content
        parsed_json = _parse_json_with_fix(result_str)
        validated_model = pydantic_model.model_validate(parsed_json)
    except (json.JSONDecodeError, Exception) as e:
        _msg = f"Failed to parse or validate LLM response: {e!s}"
        log.exception(_msg)
        raise ValueError(
            "The AI service returned an unexpected response. Please try again.",
        ) from e

    _msg = "_invoke_chain_and_parse returning"
    log.debug(_msg)
    return validated_model


def _generate_introduction_from_analysis(
    job_analysis_json: str,
    resume_content: str,
    llm: ChatOpenAI,
    original_banner: str | None = None,
) -> str:
    """Orchestrates resume analysis and introduction synthesis.

    Args:
        job_analysis_json: JSON string of pre-analyzed job requirements.
        resume_content: Full Markdown content of the resume.
        llm: Initialized ChatOpenAI client.
        original_banner: Original banner text for context (optional).

    Returns:
        Generated introduction as Markdown-formatted bullets.

    """
    from resume_editor.app.llm.models import CandidateAnalysis, GeneratedIntroduction

    _msg = "_generate_introduction_from_analysis starting"
    log.debug(_msg)

    try:
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
            original_banner=original_banner or "",
        )

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

    except ValueError as e:
        _msg = f"Failed during introduction generation: {e!s}"
        log.exception(_msg)
        introduction = ""

    _msg = "_generate_introduction_from_analysis returning"
    log.debug(_msg)
    return introduction


def generate_introduction_from_resume(
    resume_content: str,
    job_description: str,
    llm_config: object,
    original_banner: str | None = None,
) -> str:
    """Generates a resume introduction using a multi-step LLM chain.

    Args:
        resume_content: The full Markdown content of the resume.
        job_description: The job description to align with.
        llm_config: Configuration for the LLM client.
        original_banner: Original banner text for context (optional).

    Returns:
        Generated introduction as Markdown string.

    """
    from resume_editor.app.llm.models import JobKeyRequirements

    _msg = "generate_introduction_from_resume starting"
    log.debug(_msg)

    llm = initialize_llm_client(llm_config)

    try:
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

    except ValueError as e:
        _msg = f"Failed during job analysis: {e!s}"
        log.exception(_msg)
        return ""

    introduction = _generate_introduction_from_analysis(
        job_analysis_json=job_analysis.model_dump_json(),
        resume_content=resume_content,
        llm=llm,
        original_banner=original_banner,
    )

    _msg = "generate_introduction_from_resume returning"
    log.debug(_msg)
    return introduction


def _format_banner_lines(banner: GeneratedBanner) -> str:
    """Format banner bullets into Markdown lines.

    Args:
        banner: The generated banner object.

    Returns:
        Markdown-formatted banner string.

    """
    banner_lines = []
    for bullet in banner.bullets:
        banner_lines.append(f"- **{bullet.category}:** {bullet.description}")

    if banner.education_bullet:
        banner_lines.append(
            f"- **{banner.education_bullet.category}:** {banner.education_bullet.description}"
        )

    return "\n".join(banner_lines)


def _validate_running_log(running_log: RunningLog) -> bool:
    """Validate that running log has required data.

    Args:
        running_log: The running log to validate.

    Returns:
        True if valid, False otherwise.

    """
    if not running_log.job_analysis:
        _msg = "Running log has no job_analysis, cannot generate banner"
        log.warning(_msg)
        return False

    if not running_log.refined_roles:
        _msg = "Running log has no refined_roles, cannot generate banner"
        log.warning(_msg)
        return False

    return True


def generate_banner_from_running_log(
    running_log: RunningLog,
    original_resume_content: str,
    llm_config: object,
    original_banner: str | None = None,
) -> str:
    """Generate a resume banner using refined data from the RunningLog.

    Args:
        running_log: The running log containing refined roles and job analysis.
        original_resume_content: Original resume content for cross-section extraction.
        llm_config: Configuration for the LLM client.
        original_banner: Original banner text for context (optional).

    Returns:
        Generated banner as Markdown-formatted string.

    """
    _msg = "generate_banner_from_running_log starting"
    log.debug(_msg)

    if not _validate_running_log(running_log):
        return ""

    cross_section_evidence = _extract_cross_section_evidence(
        resume_content=original_resume_content,
        job_analysis=running_log.job_analysis,
    )

    llm = initialize_llm_client(llm_config)

    banner = _invoke_banner_generation_chain(
        llm=llm,
        job_analysis=running_log.job_analysis,
        refined_roles=running_log.refined_roles,
        cross_section_evidence=cross_section_evidence,
        original_banner=original_banner,
    )

    if banner is None:
        _msg = "Banner generation returned None"
        log.warning(_msg)
        return ""

    result = _format_banner_lines(banner)

    _msg = "generate_banner_from_running_log returning"
    log.debug(_msg)
    return result
