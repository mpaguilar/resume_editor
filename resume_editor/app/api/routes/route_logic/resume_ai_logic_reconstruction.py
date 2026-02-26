"""Resume reconstruction functions for resume AI logic."""

import logging

from resume_editor.app.api.routes.route_logic.resume_ai_logic_extraction import (
    _extract_raw_section,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)
from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_experience_info,
    serialize_experience_to_markdown,
)
from resume_editor.app.api.routes.route_models import ExperienceResponse
from resume_editor.app.models.resume.experience import Role

log = logging.getLogger(__name__)


def _build_resume_sections(
    raw_personal: str,
    raw_education: str,
    raw_certifications: str,
    experience_markdown: str,
) -> list[str]:
    """Build list of resume sections from raw content.

    Args:
        raw_personal: Raw personal section content.
        raw_education: Raw education section content.
        raw_certifications: Raw certifications section content.
        experience_markdown: Serialized experience section.

    Returns:
        List of section strings to combine.

    """
    sections = []
    for section in [raw_personal, raw_education, raw_certifications]:
        if section.strip():
            sections.append(section.strip() + "\n")
    sections.append(experience_markdown)
    return sections


def _update_roles_with_refined_data(
    base_roles: list[Role],
    refined_roles: dict[int, dict],
) -> list[Role]:
    """Update base roles with refined data.

    Args:
        base_roles: Original list of roles.
        refined_roles: Dictionary mapping index to refined role data.

    Returns:
        Updated list of roles.

    """
    final_roles = list(base_roles)
    for index, role_data in refined_roles.items():
        if 0 <= index < len(final_roles):
            final_roles[index] = Role.model_validate(role_data)
    return final_roles


def _reconstruct_refined_resume_content(
    params: ProcessExperienceResultParams,
) -> str:
    """Reconstructs resume markdown with refined experience roles.

    Args:
        params: Parameters containing all necessary data.

    Returns:
        The reconstructed resume content as Markdown.

    """
    _msg = "_reconstruct_refined_resume_content starting"
    log.debug(_msg)

    # Extract raw sections to preserve
    raw_personal = _extract_raw_section(params.original_resume_content, "personal")
    raw_education = _extract_raw_section(params.original_resume_content, "education")
    raw_certifications = _extract_raw_section(
        params.original_resume_content,
        "certifications",
    )

    # Extract experience from original and refinement base
    original_experience_info = extract_experience_info(params.original_resume_content)
    refinement_base_experience = extract_experience_info(
        params.resume_content_to_refine,
    )

    # Update roles with refined data
    final_roles = _update_roles_with_refined_data(
        refinement_base_experience.roles,
        params.refined_roles,
    )

    # Create final experience with refined roles and original projects
    updated_experience = ExperienceResponse(
        roles=final_roles,
        projects=original_experience_info.projects,
    )

    # Reconstruct full resume
    experience_markdown = serialize_experience_to_markdown(updated_experience)
    sections = _build_resume_sections(
        raw_personal,
        raw_education,
        raw_certifications,
        experience_markdown,
    )
    final_content = "\n".join(filter(None, sections))

    _msg = "_reconstruct_refined_resume_content returning"
    log.debug(_msg)
    return final_content


async def process_refined_experience_result(
    params: ProcessExperienceResultParams,
) -> str:
    """Process refined experience result and generate new resume content.

    Args:
        params: Parameters containing all necessary data.

    Returns:
        The processed resume content with refined experience.

    """
    _msg = "process_refined_experience_result starting"
    log.debug(_msg)

    result = _reconstruct_refined_resume_content(params)

    _msg = "process_refined_experience_result returning"
    log.debug(_msg)
    return result
