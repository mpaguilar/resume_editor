from datetime import datetime

import pytest
from pydantic import ValidationError

from resume_editor.app.models.resume.education import Degree, Degrees, Education


class TestDegree:
    """Test the Degree model."""

    def test_validate_school_valid(self):
        """Test that valid school names are accepted."""
        degree = Degree(school="University of California")
        assert degree.school == "University of California"

    def test_validate_school_empty_string(self):
        """Test that empty school names raise ValueError."""
        with pytest.raises(ValueError, match="school must not be empty"):
            Degree(school="")

    def test_validate_school_whitespace_only(self):
        """Test that whitespace-only school names raise ValueError."""
        with pytest.raises(ValueError, match="school must not be empty"):
            Degree(school="   ")

    def test_validate_school_non_string(self):
        """Test that non-string school values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            Degree(school=123)

    def test_validate_degree_none(self):
        """Test that None degree values are accepted."""
        degree = Degree(school="University", degree=None)
        assert degree.degree is None

    def test_validate_degree_valid(self):
        """Test that valid degree values are accepted."""
        degree = Degree(school="University", degree="Bachelor")
        assert degree.degree == "Bachelor"

    def test_validate_degree_empty_string(self):
        """Test that empty degree values raise ValueError."""
        with pytest.raises(ValueError, match="degree must not be empty"):
            Degree(school="University", degree="")

    def test_validate_degree_whitespace_only(self):
        """Test that whitespace-only degree values raise ValueError."""
        with pytest.raises(ValueError, match="degree must not be empty"):
            Degree(school="University", degree="   ")

    def test_validate_degree_non_string(self):
        """Test that non-string degree values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            Degree(school="University", degree=123)

    def test_validate_major_none(self):
        """Test that None major values are accepted."""
        degree = Degree(school="University", major=None)
        assert degree.major is None

    def test_validate_major_valid(self):
        """Test that valid major values are accepted."""
        degree = Degree(school="University", major="Computer Science")
        assert degree.major == "Computer Science"

    def test_validate_major_empty_string(self):
        """Test that empty major values raise ValueError."""
        with pytest.raises(ValueError, match="major must not be empty"):
            Degree(school="University", major="")

    def test_validate_major_whitespace_only(self):
        """Test that whitespace-only major values raise ValueError."""
        with pytest.raises(ValueError, match="major must not be empty"):
            Degree(school="University", major="   ")

    def test_validate_major_non_string(self):
        """Test that non-string major values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            Degree(school="University", major=123)

    def test_validate_gpa_none(self):
        """Test that None gpa values are accepted."""
        degree = Degree(school="University", gpa=None)
        assert degree.gpa is None

    def test_validate_gpa_valid(self):
        """Test that valid gpa values are accepted."""
        degree = Degree(school="University", gpa="3.8")
        assert degree.gpa == "3.8"

    def test_validate_gpa_empty_string(self):
        """Test that empty gpa values raise ValueError."""
        with pytest.raises(ValueError, match="gpa must not be empty"):
            Degree(school="University", gpa="")

    def test_validate_gpa_whitespace_only(self):
        """Test that whitespace-only gpa values raise ValueError."""
        with pytest.raises(ValueError, match="gpa must not be empty"):
            Degree(school="University", gpa="   ")

    def test_validate_gpa_non_string(self):
        """Test that non-string gpa values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid string"):
            Degree(school="University", gpa=123)

    def test_validate_dates_valid_datetime(self):
        """Test that valid datetime objects are accepted for dates."""
        date = datetime(2020, 1, 1)
        degree = Degree(school="University", start_date=date, end_date=date)
        assert degree.start_date == date
        assert degree.end_date == date

    def test_validate_dates_none(self):
        """Test that None values are accepted for dates."""
        degree = Degree(school="University", start_date=None, end_date=None)
        assert degree.start_date is None
        assert degree.end_date is None

    def test_validate_dates_invalid_type(self):
        """Test that invalid date types raise ValidationError."""
        # Pydantic automatically converts valid date strings to datetime objects
        # So this test is not applicable - Pydantic handles string conversion
        with pytest.raises(ValidationError, match="Input should be a valid datetime"):
            Degree(school="a", start_date=object())

    def test_validate_end_date_before_start_date(self):
        """Test that end_date before start_date raises ValueError."""
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2019, 1, 1)
        with pytest.raises(ValueError, match="end_date must not be before start_date"):
            Degree(school="University", start_date=start_date, end_date=end_date)

    def test_validate_end_date_valid_order(self):
        """Test that valid date order is accepted."""
        start_date = datetime(2019, 1, 1)
        end_date = datetime(2020, 1, 1)
        degree = Degree(school="University", start_date=start_date, end_date=end_date)
        assert degree.end_date == end_date


class TestDegrees:
    """Test the Degrees model."""

    def test_validate_degrees_valid_list(self):
        """Test that valid list of degrees is accepted."""
        degree1 = Degree(school="University 1")
        degree2 = Degree(school="University 2")
        degrees = Degrees(degrees=[degree1, degree2])
        assert len(degrees) == 2
        assert degrees[0] == degree1
        assert degrees[1] == degree2

    def test_validate_degrees_empty_list(self):
        """Test that empty list of degrees is accepted."""
        degrees = Degrees(degrees=[])
        assert len(degrees) == 0

    def test_validate_degrees_default(self):
        """Test that Degrees can be instantiated without arguments and defaults to empty list."""
        degrees = Degrees()
        assert degrees.degrees == []

    def test_validate_degrees_non_list(self):
        """Test that non-list degrees values raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError, match="Input should be a valid list"):
            Degrees(degrees="not a list")

    def test_validate_degrees_invalid_items(self):
        """Test that non-Degree items in list raise ValidationError."""
        # missing test
        with pytest.raises(ValidationError) as excinfo:
            Degrees(degrees=["not a degree"])
        assert "Input should be a valid dictionary or instance of Degree" in str(
            excinfo.value,
        )

    def test_iter_method(self):
        """Test the __iter__ method."""
        degree1 = Degree(school="University 1")
        degree2 = Degree(school="University 2")
        degrees = Degrees(degrees=[degree1, degree2])
        result = list(degrees)
        assert result == [degree1, degree2]

    def test_len_method(self):
        """Test the __len__ method."""
        degree1 = Degree(school="University 1")
        degree2 = Degree(school="University 2")
        degrees = Degrees(degrees=[degree1, degree2])
        assert len(degrees) == 2

    def test_getitem_method(self):
        """Test the __getitem__ method."""
        degree1 = Degree(school="University 1")
        degree2 = Degree(school="University 2")
        degrees = Degrees(degrees=[degree1, degree2])
        assert degrees[0] == degree1
        assert degrees[1] == degree2


class TestEducation:
    """Test the Education model."""

    def test_education_with_degrees(self):
        """Test Education with valid degrees."""
        degree = Degree(school="University")
        degrees = Degrees(degrees=[degree])
        education = Education(degrees=degrees)
        assert education.degrees == degrees

    def test_education_without_degrees(self):
        """Test Education with no degrees."""
        education = Education(degrees=None)
        assert education.degrees is None
