import io
from unittest.mock import MagicMock, patch

import pytest
from resume_writer.resume_render.render_settings import ResumeRenderSettings

from resume_editor.app.api.routes.route_logic.resume_export import (
    render_resume_to_docx_stream,
)


@patch("resume_editor.app.api.routes.route_logic.resume_export.AtsRenderResume")
@patch("resume_editor.app.api.routes.route_logic.resume_export.docx.Document")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_ats_format(
    mock_parse, mock_docx_document, mock_ats_renderer
):
    """Test render_resume_to_docx_stream with 'ats' format."""
    # Arrange
    mock_resume_content = "# Resume"
    mock_settings = {"font_size": "12"}
    mock_parsed_resume = MagicMock()
    mock_parse.return_value = mock_parsed_resume

    mock_doc = MagicMock()
    mock_docx_document.return_value = mock_doc

    mock_renderer_instance = MagicMock()
    mock_renderer_instance.document = mock_doc
    mock_ats_renderer.return_value = mock_renderer_instance

    # Act
    result_buffer = render_resume_to_docx_stream(
        resume_content=mock_resume_content,
        render_format="ats",
        settings_dict=mock_settings,
    )

    # Assert
    mock_parse.assert_called_once_with(markdown_content=mock_resume_content)
    mock_docx_document.assert_called_once()
    mock_ats_renderer.assert_called_once()

    args, kwargs = mock_ats_renderer.call_args
    assert kwargs["resume"] == mock_parsed_resume
    assert kwargs["document"] == mock_doc
    render_settings_arg = kwargs["settings"]
    assert isinstance(render_settings_arg, ResumeRenderSettings)
    assert render_settings_arg.font_size == "12"

    mock_renderer_instance.render.assert_called_once()
    mock_renderer_instance.document.save.assert_called_once_with(result_buffer)
    assert isinstance(result_buffer, io.BytesIO)
    assert result_buffer.tell() == 0


@pytest.mark.parametrize("render_format", ["plain", "executive_summary"])
@patch("resume_editor.app.api.routes.route_logic.resume_export.PlainRenderResume")
@patch("resume_editor.app.api.routes.route_logic.resume_export.docx.Document")
@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_plain_based_formats(
    mock_parse, mock_docx_document, mock_plain_renderer, render_format
):
    """Test render_resume_to_docx_stream with plain-based formats."""
    # Arrange
    mock_resume_content = "# Resume"
    mock_settings = {"font_size": "10"}
    mock_parsed_resume = MagicMock()
    mock_parse.return_value = mock_parsed_resume

    mock_doc = MagicMock()
    mock_docx_document.return_value = mock_doc

    mock_renderer_instance = MagicMock()
    mock_renderer_instance.document = mock_doc
    mock_plain_renderer.return_value = mock_renderer_instance

    # Act
    result_buffer = render_resume_to_docx_stream(
        resume_content=mock_resume_content,
        render_format=render_format,
        settings_dict=mock_settings,
    )

    # Assert
    mock_parse.assert_called_once_with(markdown_content=mock_resume_content)
    mock_docx_document.assert_called_once()
    mock_plain_renderer.assert_called_once()

    args, kwargs = mock_plain_renderer.call_args
    assert kwargs["resume"] == mock_parsed_resume
    assert kwargs["document"] == mock_doc
    render_settings_arg = kwargs["settings"]
    assert isinstance(render_settings_arg, ResumeRenderSettings)
    assert render_settings_arg.font_size == "10"

    mock_renderer_instance.render.assert_called_once()
    mock_renderer_instance.document.save.assert_called_once_with(result_buffer)
    assert isinstance(result_buffer, io.BytesIO)
    assert result_buffer.tell() == 0


@patch(
    "resume_editor.app.api.routes.route_logic.resume_export.parse_resume_to_writer_object"
)
def test_render_resume_to_docx_stream_invalid_format(mock_parse):
    """Test render_resume_to_docx_stream raises ValueError for invalid format."""
    mock_parse.return_value = MagicMock()
    with pytest.raises(ValueError, match="Unknown render format: invalid"):
        render_resume_to_docx_stream(
            resume_content="# Resume", render_format="invalid", settings_dict={}
        )
