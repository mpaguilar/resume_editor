import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def _date_format_filter(value: datetime | None, format_string: str = "%Y-%m-%d") -> str:
    """Jinja2 filter to format a datetime object as a string."""
    if value is None:
        return ""
    return value.strftime(format_string)


env.filters["date_format"] = _date_format_filter
env.filters["strftime"] = _date_format_filter


def _generate_resume_list_html(
    base_resumes: list[DatabaseResume],
    refined_resumes: list[DatabaseResume],
    selected_resume_id: int | None = None,
    sort_by: str | None = None,
    wrap_in_div: bool = False,
) -> str:
    """
    Generates HTML for a list of resumes, optionally marking one as selected.

    Args:
        base_resumes (list[DatabaseResume]): The list of base resumes to display.
        refined_resumes (list[DatabaseResume]): The list of refined resumes to display.
        selected_resume_id (int | None): The ID of the resume to mark as selected.

    Returns:
        str: HTML string for the resume list.

    Notes:
        1. Renders the `partials/resume/_resume_list.html` template.

    """
    template = env.get_template("partials/resume/_resume_list.html")
    rendered_html = template.render(
        base_resumes=base_resumes,
        refined_resumes=refined_resumes,
        selected_resume_id=selected_resume_id,
        sort_by=sort_by,
    )
    if wrap_in_div:
        return f'<div id="resume-list">{rendered_html}</div>'
    return rendered_html


def _generate_resume_detail_html(resume: DatabaseResume) -> str:
    """
    Generate the HTML for the resume detail view.

    Args:
        resume (DatabaseResume): The resume object to generate HTML for.

    Returns:
        str: HTML string for the resume detail view.

    Notes:
        1. Renders the `partials/resume/_resume_detail.html` template.
    """
    template = env.get_template("partials/resume/_resume_detail.html")
    return template.render(resume=resume)


def _create_refine_result_html(
    resume_id: int,
    target_section_val: str,
    refined_content: str,
    job_description: str | None = None,
) -> str:
    """
    Creates the HTML for the refinement result container with controls.

    Args:
        resume_id (int): The ID of the resume being refined.
        target_section_val (str): The name of the section that was refined.
        refined_content (str): The new Markdown content for the section.
        job_description (str | None): The job description used for refinement.

    Returns:
        str: An HTML snippet containing a form with the refined content
             in a textarea and buttons to accept, reject, or save as new.

    Notes:
        1. Renders the `partials/resume/_refine_result.html` template.

    """
    template = env.get_template("partials/resume/_refine_result.html")
    return template.render(
        resume_id=resume_id,
        target_section_val=target_section_val,
        refined_content=refined_content,
        job_description=job_description,
    )
