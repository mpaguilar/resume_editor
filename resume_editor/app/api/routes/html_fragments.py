import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def _generate_resume_list_html(
    resumes: list[DatabaseResume], selected_resume_id: int | None = None
) -> str:
    """
    Generates HTML for a list of resumes, optionally marking one as selected.

    Args:
        resumes (list[DatabaseResume]): The list of resumes to display.
        selected_resume_id (int | None): The ID of the resume to mark as selected.

    Returns:
        str: HTML string for the resume list.

    Notes:
        1. Renders the `partials/resume/_resume_list.html` template.

    """
    template = env.get_template("partials/resume/_resume_list.html")
    return template.render(resumes=resumes, selected_resume_id=selected_resume_id)


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
    resume_id: int, target_section_val: str, refined_content: str
) -> str:
    """
    Creates the HTML for the refinement result container with controls.

    Args:
        resume_id (int): The ID of the resume being refined.
        target_section_val (str): The name of the section that was refined.
        refined_content (str): The new Markdown content for the section.

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
    )
