import logging
from typing import Any, Callable

from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)

log = logging.getLogger(__name__)


def _serialize_section_if_present(
    section_data: Any,
    serializer: Callable[[Any], str],
) -> str | None:
    """Serialize a resume section if data is present.

    Args:
        section_data (Any): The section data to serialize, or None.
        serializer (Callable): The function to serialize the section.

    Returns:
        str | None: The serialized section string, or None if section_data is None or empty.

    Notes:
        1. If section_data is None, return None.
        2. Otherwise, call the serializer function with section_data.
        3. Return the result if it's truthy, otherwise return None.

    """
    if section_data is None:
        return None
    serialized = serializer(section_data)
    return serialized if serialized else None


def _collect_resume_sections(
    personal_info: PersonalInfoResponse | None,
    education: EducationResponse | None,
    certifications: CertificationsResponse | None,
    experience: ExperienceResponse | None,
) -> list[str]:
    """Collect all non-empty resume sections into a list.

    Args:
        personal_info (PersonalInfoResponse | None): Personal information data.
        education (EducationResponse | None): Education information data.
        certifications (CertificationsResponse | None): Certifications information data.
        experience (ExperienceResponse | None): Experience information data.

    Returns:
        list[str]: A list of serialized section strings.

    Notes:
        1. Import serialization functions.
        2. Serialize each section if present using _serialize_section_if_present.
        3. Collect all non-None results into a list.
        4. Return the list of serialized sections.

    """
    from resume_editor.app.api.routes.route_logic.resume_serialization import (
        serialize_certifications_to_markdown,
        serialize_education_to_markdown,
        serialize_experience_to_markdown,
        serialize_personal_info_to_markdown,
    )

    sections = []

    personal_section = _serialize_section_if_present(
        personal_info,
        serialize_personal_info_to_markdown,
    )
    if personal_section:
        sections.append(personal_section)

    education_section = _serialize_section_if_present(
        education,
        serialize_education_to_markdown,
    )
    if education_section:
        sections.append(education_section)

    certifications_section = _serialize_section_if_present(
        certifications,
        serialize_certifications_to_markdown,
    )
    if certifications_section:
        sections.append(certifications_section)

    experience_section = _serialize_section_if_present(
        experience,
        serialize_experience_to_markdown,
    )
    if experience_section:
        sections.append(experience_section)

    return sections


def reconstruct_resume_markdown(
    personal_info: PersonalInfoResponse | None = None,
    education: EducationResponse | None = None,
    certifications: CertificationsResponse | None = None,
    experience: ExperienceResponse | None = None,
) -> str:
    """Reconstruct a complete resume Markdown document from structured data sections.

    Args:
        personal_info (PersonalInfoResponse | None): Personal information data structure. If None, the personal info section is omitted.
        education (EducationResponse | None): Education information data structure. If None, the education section is omitted.
        certifications (CertificationsResponse | None): Certifications information data structure. If None, the certifications section is omitted.
        experience (ExperienceResponse | None): Experience information data structure, containing roles and projects. If None, the experience section is omitted.

    Returns:
        str: A complete Markdown formatted resume document with all provided sections joined by double newlines.

    Notes:
        1. Collect all sections using _collect_resume_sections.
        2. Filter out any empty strings and strip whitespace from each section.
        3. Join all sections with double newlines to ensure proper spacing.
        4. Return the complete Markdown resume content.
        5. No network, disk, or database access is performed.

    """
    sections = _collect_resume_sections(
        personal_info,
        education,
        certifications,
        experience,
    )

    return "\n\n".join(filter(None, [s.strip() for s in sections]))


def build_complete_resume_from_sections(
    personal_info: PersonalInfoResponse,
    education: EducationResponse,
    certifications: CertificationsResponse,
    experience: ExperienceResponse,
) -> str:
    """Build a complete resume Markdown document from all structured sections.

    Args:
        personal_info (PersonalInfoResponse): Personal information data structure.
        education (EducationResponse): Education information data structure.
        certifications (CertificationsResponse): Certifications information data structure.
        experience (ExperienceResponse): Experience information data structure.

    Returns:
        str: A complete Markdown formatted resume document with all sections in the order: personal, education, certifications, experience.

    Notes:
        1. Calls reconstruct_resume_markdown with all sections.
        2. Ensures proper section ordering (personal, education, certifications, experience).
        3. Returns the complete Markdown resume content.
        4. No network, disk, or database access is performed.

    """
    return reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education,
        certifications=certifications,
        experience=experience,
    )
