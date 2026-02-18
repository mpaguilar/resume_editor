from unittest.mock import MagicMock

import pytest

from resume_editor.app.utils.filename_utils import (
    generate_resume_filename,
    sanitize_filename_component,
)


# Tests for sanitize_filename_component
def test_sanitize_filename_component_replaces_spaces():
    """Test that spaces are replaced with underscores."""
    assert sanitize_filename_component("John Doe") == "John_Doe"


def test_sanitize_filename_component_replaces_invalid_chars():
    """Test that invalid characters are replaced with underscores."""
    assert sanitize_filename_component("file/name!@#$%.txt") == "file_name.txt"


def test_sanitize_filename_component_collapses_underscores():
    """Test that multiple consecutive underscores are collapsed to one."""
    assert sanitize_filename_component("file___name") == "file_name"


def test_sanitize_filename_component_strips_leading_trailing_underscores():
    """Test that leading and trailing underscores are removed."""
    assert sanitize_filename_component("_filename_") == "filename"


def test_sanitize_filename_component_preserves_case():
    """Test that character case is preserved."""
    assert sanitize_filename_component("JohnDoeResumeV2") == "JohnDoeResumeV2"


@pytest.mark.parametrize(
    "input_str, expected_output",
    [
        ("  My Resume (Final) v2!.docx  ", "My_Resume_Final_v2.docx"),
        ("---John's_Resume---", "Johns_Resume"),
        ("file/with/path", "file_with_path"),
        ("a___b...c", "a_b.c"),  # period is allowed
        ("__multiple__underscores__", "multiple_underscores"),
    ],
)
def test_sanitize_filename_component_comprehensive(input_str, expected_output):
    """Test a combination of all sanitization rules."""
    assert sanitize_filename_component(input_str) == expected_output


# Tests for generate_resume_filename
def test_generate_resume_filename_base_resume():
    """Test filename generation for a base resume."""
    mock_resume_db = MagicMock()
    mock_resume_db.name = "My Base Resume"
    mock_resume_db.is_base = True

    mock_resume_writer = MagicMock()

    filename = generate_resume_filename(mock_resume_db, mock_resume_writer, "docx")
    assert filename == "My_Base_Resume.docx"


def test_generate_resume_filename_refined_resume():
    """Test filename generation for a refined resume with a candidate name."""
    mock_resume_db = MagicMock()
    mock_resume_db.name = "Tailored for Acme Corp"
    mock_resume_db.is_base = False

    mock_resume_writer = MagicMock()
    mock_resume_writer.personal.contact_info.name = "John Doe"

    filename = generate_resume_filename(mock_resume_db, mock_resume_writer, "md")
    assert filename == "John_Doe_Tailored_for_Acme_Corp.md"


def test_generate_resume_filename_refined_resume_no_candidate_name():
    """Test fallback for a refined resume when candidate name is missing."""
    mock_resume_db = MagicMock()
    mock_resume_db.name = "Tailored for Acme Corp"
    mock_resume_db.is_base = False

    # Simulate missing name
    mock_resume_writer = MagicMock()
    mock_resume_writer.personal.contact_info.name = None

    filename = generate_resume_filename(mock_resume_db, mock_resume_writer, "docx")
    assert filename == "Tailored_for_Acme_Corp.docx"

    # Simulate missing contact_info
    mock_resume_writer.personal.contact_info = None
    filename = generate_resume_filename(mock_resume_db, mock_resume_writer, "docx")
    assert filename == "Tailored_for_Acme_Corp.docx"

    # Simulate missing personal
    mock_resume_writer.personal = None
    filename = generate_resume_filename(mock_resume_db, mock_resume_writer, "docx")
    assert filename == "Tailored_for_Acme_Corp.docx"


def test_generate_resume_filename_with_sanitization():
    """Test that components are sanitized during filename generation."""
    # Refined resume with sanitization needed
    mock_resume_db_refined = MagicMock()
    mock_resume_db_refined.name = "Resume for 'Big Corp'!"
    mock_resume_db_refined.is_base = False

    mock_resume_writer = MagicMock()
    mock_resume_writer.personal.contact_info.name = "Jane / Doe"

    filename = generate_resume_filename(
        mock_resume_db_refined, mock_resume_writer, "pdf"
    )
    assert filename == "Jane_Doe_Resume_for_Big_Corp.pdf"

    # Base resume with sanitization needed
    mock_resume_db_base = MagicMock()
    mock_resume_db_base.name = "  My Main / Base Resume "
    mock_resume_db_base.is_base = True

    filename = generate_resume_filename(mock_resume_db_base, mock_resume_writer, "txt")
    assert filename == "My_Main_Base_Resume.txt"
