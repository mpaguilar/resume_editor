import io
import logging

import docx
from resume_writer.models.resume import Resume as WriterResume
from resume_writer.resume_render.render_settings import ResumeRenderSettings
from resume_writer.resume_render.ats.resume_main import (
    RenderResume as AtsRenderResume,
)
from resume_writer.resume_render.plain.resume_main import (
    RenderResume as PlainRenderResume,
)

from resume_editor.app.api.routes.route_logic.resume_parsing import (
    parse_resume_to_writer_object,
)

log = logging.getLogger(__name__)


def render_resume_to_docx_stream(
    resume_content: str, render_format: str, settings_dict: dict
) -> io.BytesIO:
    """Renders a resume's markdown content to a DOCX file stream.

    This function parses resume markdown, applies render settings, and uses the
    appropriate renderer to generate a DOCX file into an in-memory buffer.

    Args:
        resume_content (str): The markdown content of the resume.
        render_format (str): The rendering format, either "plain" or "ats".
        settings_dict (dict): A dictionary of settings to apply to the render.

    Returns:
        io.BytesIO: An in-memory buffer containing the generated DOCX file.

    Raises:
        ValueError: If an unknown render_format is provided.

    Notes:
        1. Parse the `resume_content` into a `resume_writer` `Resume` object.
        2. Instantiate `ResumeRenderSettings` and update it with `settings_dict`.
        3. Create an in-memory `io.BytesIO` buffer.
        4. Create a `docx.Document` object.
        5. Based on `render_format`, instantiate `AtsRenderResume` or `PlainRenderResume`.
        6. Invoke the renderer's `render()` method.
        7. Save the generated document to the buffer.
        8. Reset the buffer's position to the start.
        9. Return the buffer.

    """
    _msg = "render_resume_to_docx_stream starting"
    log.debug(_msg)

    # 1. Parse resume content
    parsed_resume: WriterResume = parse_resume_to_writer_object(
        markdown_content=resume_content
    )

    # 2. Instantiate and update render settings
    render_settings = ResumeRenderSettings(default_init=True)
    render_settings.update_from_dict(settings_dict)

    # 3. Create buffer
    buffer = io.BytesIO()

    # 4. Create Document
    document = docx.Document()

    # 5. Instantiate renderer
    renderer = None
    if render_format == "plain" or render_format == "executive_summary":
        renderer = PlainRenderResume(
            resume=parsed_resume, document=document, settings=render_settings
        )
    elif render_format == "ats":
        renderer = AtsRenderResume(
            resume=parsed_resume, document=document, settings=render_settings
        )
    else:
        _msg = f"Unknown render format: {render_format}"
        log.error(_msg)
        raise ValueError(_msg)

    # 6. Render
    renderer.render()

    # 7. Save to buffer
    renderer.document.save(buffer)

    # 8. Reset buffer position
    buffer.seek(0)

    _msg = "render_resume_to_docx_stream returning"
    log.debug(_msg)
    # 9. Return buffer
    return buffer
