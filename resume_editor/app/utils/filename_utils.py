import re
import typing

if typing.TYPE_CHECKING:
    from resume_writer.models.resume import Resume as WriterResume

    from resume_editor.app.models.resume_model import Resume as DatabaseResume


def sanitize_filename_component(component: str) -> str:
    """Sanitizes a string component for use in a filename.

    The sanitization logic is as follows:
    1. Trims leading/trailing whitespace and removes apostrophes.
    2. Replaces spaces and any character that is not an ASCII letter, number,
       underscore, or period with a single underscore.
    3. Collapses any sequence of multiple underscores into a single one.
    4. Collapses any sequence of multiple periods into a single one.
    5. Removes any underscores immediately preceding a period.
    6. Removes any leading or trailing underscores from the resulting string.
    Case is preserved throughout.

    Args:
        component (str): The string component to sanitize.

    Returns:
        str: The sanitized string component.

    """
    # 1. Tidy up input string
    sanitized = component.strip().replace("'", "")

    # 2. Replace spaces and invalid characters with underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_.]|\s", "_", sanitized)

    # 3. Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # 4. Collapse multiple periods
    sanitized = re.sub(r"\.+", ".", sanitized)

    # 5. Remove underscores before periods
    sanitized = re.sub(r"_+\.", ".", sanitized)

    # 6. Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    return sanitized


def generate_resume_filename(
    resume_db: "DatabaseResume",
    resume_writer: "WriterResume",
    extension: str,
) -> str:
    """Generates a sanitized filename for a resume.

    The filename format depends on whether the resume is a "base" or "refined" version.

    - For base resumes (`is_base=True`), the format is:
      `{sanitized_resume_name}.{extension}`
    - For refined resumes (`is_base=False`), the format is:
      `{sanitized_candidate_name}_{sanitized_resume_name}.{extension}`

    If a refined resume is processed but the candidate's name is not found in the
    parsed resume_writer object, it gracefully falls back to the base resume format.

    Args:
        resume_db ("DatabaseResume"): The database model instance for the resume.
        resume_writer ("WriterResume"): The parsed `resume_writer` object.
        extension (str): The file extension to use (e.g., "docx", "md").

    Returns:
        str: The generated, sanitized filename.

    """
    sanitized_resume_name = sanitize_filename_component(resume_db.name)

    if not resume_db.is_base:
        candidate_name = None
        if (
            resume_writer
            and resume_writer.personal
            and resume_writer.personal.contact_info
            and resume_writer.personal.contact_info.name
        ):
            candidate_name = resume_writer.personal.contact_info.name

        if candidate_name:
            sanitized_candidate_name = sanitize_filename_component(candidate_name)
            return f"{sanitized_candidate_name}_{sanitized_resume_name}.{extension}"

    # Fallback for base resumes or refined resumes without a candidate name
    return f"{sanitized_resume_name}.{extension}"
