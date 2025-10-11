import datetime
import textwrap
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_education_info,
    serialize_education_to_markdown,
)
from resume_editor.app.api.routes.route_models import EducationResponse


def test_serialize_education_to_markdown_partial_data_with_degree():
    """Test serializing education to cover the 'degree' field presence."""
    education = EducationResponse(
        degrees=[
            {
                "school": "A University",
                "degree": "B.Sc.",
            },
        ],
    )
    markdown = serialize_education_to_markdown(education)
    assert "Degree: B.Sc." in markdown


def test_serialize_education_to_markdown_degree_without_school():
    """Test serializing education where a degree has no school but has a degree name."""
    mock_degree = Mock()
    mock_degree.school = None
    mock_degree.degree = "Ph.D. in Computer Science"
    mock_degree.major = None
    mock_degree.start_date = None
    mock_degree.end_date = None
    mock_degree.gpa = None

    mock_education = Mock()
    mock_education.degrees = [mock_degree]

    markdown = serialize_education_to_markdown(mock_education)
    expected = textwrap.dedent(
        """\
    # Education

    ## Degrees

    ### Degree

    Degree: Ph.D. in Computer Science

    """,
    )
    assert markdown == expected


class TestExtractEducationInfo:
    """Test cases for education info extraction functions."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_no_education_section(self, mock_parse):
        """Test education info extraction when education section is missing."""
        mock_resume = Mock()
        mock_resume.education = None
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert response.degrees == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_no_degrees(self, mock_parse):
        """Test education info extraction when degrees are missing."""
        mock_education = Mock()
        mock_education.degrees = None
        mock_resume = Mock()
        mock_resume.education = mock_education
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert response.degrees == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_education_info_partial_data(self, mock_parse):
        """Test education info extraction with partial data in a degree."""
        test_date = datetime.datetime(2022, 1, 1, 0, 0)
        mock_degree = Mock()
        mock_degree.school = "Partial Uni"
        mock_degree.degree = None
        mock_degree.major = "Partial Major"
        mock_degree.start_date = None
        mock_degree.end_date = test_date
        mock_degree.gpa = None

        mock_education = Mock()
        mock_education.degrees = [mock_degree]
        mock_resume = Mock()
        mock_resume.education = mock_education
        mock_parse.return_value = mock_resume

        response = extract_education_info("any content")
        assert len(response.degrees) == 1
        degree = response.degrees[0]
        assert degree.school == "Partial Uni"
        assert degree.degree is None
        assert degree.major == "Partial Major"
        assert degree.start_date is None
        assert degree.end_date == test_date
        assert degree.gpa is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_education_info_parse_fails(self, mock_parse):
        """Test education info extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse education info"):
            extract_education_info("invalid content")


def test_serialize_education_to_markdown_none_input():
    """Test serialize_education_to_markdown with None input - covers line 402."""
    result = serialize_education_to_markdown(None)
    assert result == ""


def test_serialize_education_to_markdown_empty():
    """Test serialization of empty education information to Markdown."""
    education = EducationResponse(degrees=[])
    markdown = serialize_education_to_markdown(education)
    assert markdown == ""


def test_serialize_education_to_markdown_partial_data():
    """Test serialization of partial education information to Markdown."""
    education = EducationResponse(
        degrees=[
            {
                "school": "Partial University",
                "degree": None,
                "major": "Partial Major",
                "start_date": "2018-01-01",
                "end_date": None,
                "gpa": None,
            },
        ],
    )

    markdown = serialize_education_to_markdown(education)
    expected = """# Education

## Degrees

### Degree

School: Partial University
Major: Partial Major
Start date: 01/2018

"""
    assert markdown == expected

def test_serialize_education_with_all_fields():
    """Test serializing an education section with all possible fields."""
    education = EducationResponse(
        degrees=[
            {
                "school": "University of All Fields",
                "degree": "PhD",
                "major": "Comprehensiveness",
                "start_date": "2018-09-01",
                "end_date": "2022-05-01",
                "gpa": "4.0",
            }
        ]
    )
    result = serialize_education_to_markdown(education)
    expected = textwrap.dedent(
        """\
        # Education

        ## Degrees

        ### Degree

        School: University of All Fields
        Degree: PhD
        Major: Comprehensiveness
        Start date: 09/2018
        End date: 05/2022
        GPA: 4.0

        """
    )
    assert result == expected
