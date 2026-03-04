import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from resume_editor.app.models.resume_model import Resume as DatabaseResume

log = logging.getLogger(__name__)


class RefineResultParams(BaseModel):
    """Parameters for creating the refine result HTML."""

    resume_id: int
    refined_content: str
    introduction: str | None = None
    job_description: str | None = None
    limit_refinement_years: int | None = None
    company: str | None = None
    notes: str | None = None
    extracted_company_name: str | None = None
    extracted_job_title: str | None = None
    extracted_pay_rate: str | None = None
    extracted_contact_info: str | None = None
    extracted_work_arrangement: str | None = None
    extracted_location: str | None = None
    extracted_special_instructions: str | None = None


@dataclass
class GenerateResumeListHtmlParams:
    """Parameters for _generate_resume_list_html function."""

    base_resumes: list[DatabaseResume]
    refined_resumes: list[DatabaseResume]
    selected_resume_id: int | None = None
    sort_by: str | None = None
    week_offset: int = 0
    has_older_resumes: bool = False
    has_newer_resumes: bool = False
    current_filter: str | None = None
    week_start: datetime | None = None
    week_end: datetime | None = None
    wrap_in_div: bool = False


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
    params: GenerateResumeListHtmlParams,
) -> str:
    """Generates HTML for a list of resumes, optionally marking one as selected.

    Args:
        params: The parameters for generating the resume list HTML.

    Returns:
        str: HTML string for the resume list.

    Notes:
        1. Renders the `partials/resume/_resume_list.html` template.
        2. Passes pagination and filter state for HTMX integration.
        3. Week range dates are formatted for display in the template.

    """
    template = env.get_template("partials/resume/_resume_list.html")
    rendered_html = template.render(
        base_resumes=params.base_resumes,
        refined_resumes=params.refined_resumes,
        selected_resume_id=params.selected_resume_id,
        sort_by=params.sort_by,
        week_offset=params.week_offset,
        has_older_resumes=params.has_older_resumes,
        has_newer_resumes=params.has_newer_resumes,
        current_filter=params.current_filter,
        week_start=params.week_start,
        week_end=params.week_end,
    )
    if params.wrap_in_div:
        return f'<div id="resume-list">{rendered_html}</div>'
    return rendered_html


def _generate_resume_detail_html(resume: DatabaseResume) -> str:
    """Generate the HTML for the resume detail view.

    Args:
        resume (DatabaseResume): The resume object to generate HTML for.

    Returns:
        str: HTML string for the resume detail view.

    Notes:
        1. Renders the `partials/resume/_resume_detail.html` template.

    """
    template = env.get_template("partials/resume/_resume_detail.html")
    return template.render(resume=resume)


def _create_refine_result_html(params: RefineResultParams) -> str:
    """Creates the HTML for the refinement result container with controls.

    Args:
        params (RefineResultParams): Parameters for rendering the template.

    Returns:
        str: An HTML snippet containing a form with the refined content
             in a textarea and buttons to accept, reject, or save as new.

    Notes:
        1. Renders the `partials/resume/_refine_result.html` template.

    """
    template = env.get_template("partials/resume/_refine_result.html")
    return template.render(**params.model_dump())
