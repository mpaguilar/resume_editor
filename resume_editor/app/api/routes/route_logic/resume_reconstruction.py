import logging

from resume_editor.app.api.routes.route_models import (
    CertificationsResponse,
    EducationResponse,
    ExperienceResponse,
    PersonalInfoResponse,
)

log = logging.getLogger(__name__)


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
        1. Initialize an empty list to collect resume sections.
        2. Serialize each provided section using the corresponding serialization function.
        3. Append each serialized section to the sections list if it is not empty.
        4. Filter out any empty strings and strip whitespace from each section.
        5. Join all sections with double newlines to ensure proper spacing.
        6. Return the complete Markdown resume content.
        7. No network, disk, or database access is performed.

    """
    from resume_editor.app.api.routes.route_logic.resume_serialization import (
        serialize_certifications_to_markdown,
        serialize_education_to_markdown,
        serialize_experience_to_markdown,
        serialize_personal_info_to_markdown,
    )

    sections = []

    # Serialize each section if provided
    if personal_info is not None:
        personal_section = serialize_personal_info_to_markdown(personal_info)
        if personal_section:
            sections.append(personal_section)

    if education is not None:
        education_section = serialize_education_to_markdown(education)
        if education_section:
            sections.append(education_section)

    if certifications is not None:
        certifications_section = serialize_certifications_to_markdown(certifications)
        if certifications_section:
            sections.append(certifications_section)

    if experience is not None:
        experience_section = serialize_experience_to_markdown(experience)
        if experience_section:
            sections.append(experience_section)

    # Join all sections with proper spacing
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
