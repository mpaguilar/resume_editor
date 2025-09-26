import io
from unittest.mock import MagicMock, patch

import pytest
from resume_writer.models.resume import Resume as WriterResume

from resume_editor.app.api.routes.route_logic.resume_export import (
    render_resume_to_docx_stream,
)


@patch("resume_editor.app.api.routes.route_logic.resume_export.AtsRenderResume")
@patch("resume_editor.app.api.routes.route_logic.resume_export.docx")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_ats_format(
    mock_parse, mock_docx, mock_ats_renderer
):
    """Test render_resume_to_docx_stream with 'ats' format."""
    # Arrange
    resume_content = "some resume content"
    settings_dict = {"font_size": "12"}
    mock_parsed_resume = MagicMock(spec=WriterResume)
    mock_parse.return_value = mock_parsed_resume
    mock_document = MagicMock()
    mock_docx.Document.return_value = mock_document
    mock_renderer_instance = mock_ats_renderer.return_value

    # Act
    buffer = render_resume_to_docx_stream(
        resume_content=resume_content, render_format="ats", settings_dict=settings_dict
    )

    # Assert
    mock_parse.assert_called_once_with(markdown_content=resume_content)
    mock_docx.Document.assert_called_once()
    mock_ats_renderer.assert_called_once()
    assert mock_ats_renderer.call_args[1]["resume"] == mock_parsed_resume
    assert mock_ats_renderer.call_args[1]["document"] == mock_document
    mock_renderer_instance.render.assert_called_once()
    mock_renderer_instance.document.save.assert_called_once_with(buffer)
    assert isinstance(buffer, io.BytesIO)
    assert buffer.tell() == 0


@pytest.mark.parametrize(
    "render_format",
    [
        "plain",
        "executive_summary",
    ],
)
@patch("resume_editor.app.api.routes.route_logic.resume_export.PlainRenderResume")
@patch("resume_editor.app.api.routes.route_logic.resume_export.docx")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_plain_based_formats(
    mock_parse, mock_docx, mock_plain_renderer, render_format
):
    """Test render_resume_to_docx_stream with plain-based formats."""
    # Arrange
    resume_content = "some resume content"
    settings_dict = {"font_size": "12"}
    mock_parsed_resume = MagicMock(spec=WriterResume)
    mock_parse.return_value = mock_parsed_resume
    mock_document = MagicMock()
    mock_docx.Document.return_value = mock_document
    mock_renderer_instance = mock_plain_renderer.return_value

    # Act
    buffer = render_resume_to_docx_stream(
        resume_content=resume_content,
        render_format=render_format,
        settings_dict=settings_dict,
    )

    # Assert
    mock_parse.assert_called_once_with(markdown_content=resume_content)
    mock_docx.Document.assert_called_once()
    mock_plain_renderer.assert_called_once()
    assert mock_plain_renderer.call_args[1]["resume"] == mock_parsed_resume
    assert mock_plain_renderer.call_args[1]["document"] == mock_document
    mock_renderer_instance.render.assert_called_once()
    mock_renderer_instance.document.save.assert_called_once_with(buffer)
    assert isinstance(buffer, io.BytesIO)
    assert buffer.tell() == 0


@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_invalid_format(mock_parse):
    """Test render_resume_to_docx_stream raises ValueError for invalid format."""
    # Arrange
    resume_content = "some resume content"
    settings_dict = {}

    # Act & Assert
    with pytest.raises(ValueError, match="Unknown render format: invalid"):
        render_resume_to_docx_stream(
            resume_content=resume_content,
            render_format="invalid",
            settings_dict=settings_dict,
        )
    mock_parse.assert_called_once_with(markdown_content=resume_content)
