import logging
from datetime import datetime

from pydantic import BaseModel, ValidationInfo, field_validator

log = logging.getLogger(__name__)


class Degree(BaseModel):
    """Represents details of a specific academic degree earned.

    Attributes:
        school (str): The name of the educational institution.
        degree (str | None): The type of degree (e.g., Bachelor, Master).
        start_date (datetime | None): The start date of the program.
        end_date (datetime | None): The end date of the program.
        major (str | None): The major field of study.
        gpa (str | None): The grade point average.

    """

    school: str
    degree: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    major: str | None = None
    gpa: str | None = None

    @field_validator("school")
    @classmethod
    def validate_school(cls, v: str):
        """Validate the school field.

        Args:
            v (str): The school value to validate. Must be a non-empty string.

        Returns:
            str: The validated school (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the school is empty or contains only whitespace.

        Notes:
            1. Ensure school is a string.
            2. Ensure school is not empty after stripping whitespace.

        """
        if not v.strip():
            raise ValueError("school must not be empty")
        return v.strip()

    @field_validator("degree")
    @classmethod
    def validate_degree(cls, v: str | None):
        """Validate the degree field.

        Args:
            v (str | None): The degree value to validate. Must be a non-empty string or None.

        Returns:
            str | None: The validated degree (stripped of leading/trailing whitespace) or None.

        Raises:
            ValueError: If the degree is empty after stripping whitespace.

        Notes:
            1. Ensure degree is a string or None.
            2. Ensure degree is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not v.strip():
            raise ValueError("degree must not be empty")
        return v.strip()

    @field_validator("major")
    @classmethod
    def validate_major(cls, v: str | None):
        """Validate the major field.

        Args:
            v (str | None): The major value to validate. Must be a non-empty string or None.

        Returns:
            str | None: The validated major (stripped of leading/trailing whitespace) or None.

        Raises:
            ValueError: If the major is empty after stripping whitespace.

        Notes:
            1. Ensure major is a string or None.
            2. Ensure major is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not v.strip():
            raise ValueError("major must not be empty")
        return v.strip()

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v: str | None):
        """Validate the gpa field.

        Args:
            v (str | None): The gpa value to validate. Must be a non-empty string or None.

        Returns:
            str | None: The validated gpa (stripped of leading/trailing whitespace) or None.

        Raises:
            ValueError: If the gpa is empty after stripping whitespace.

        Notes:
            1. Ensure gpa is a string or None.
            2. Ensure gpa is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not v.strip():
            raise ValueError("gpa must not be empty")
        return v.strip()

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime | None, info: ValidationInfo):
        """Validate that start_date is not after end_date.

        Args:
            v (datetime | None): The end_date value to validate.
            info (ValidationInfo): Validation info containing data.

        Returns:
            datetime | None: The validated end_date.

        Raises:
            ValueError: If end_date is before start_date.

        Notes:
            1. If both start_date and end_date are provided, ensure start_date is not after end_date.

        """
        if v is not None:
            start_date = info.data.get("start_date")
            if start_date is not None and v < start_date:
                raise ValueError("end_date must not be before start_date")
        return v


class Degrees(BaseModel):
    """Represents a collection of academic degrees earned.

    Attributes:
        degrees (list[Degree]): A list of Degree objects representing educational achievements.

    """

    degrees: list[Degree] = []

    def __iter__(self):
        """Iterate over the degrees.

        Returns:
            Iterator: An iterator over the degrees list.

        Notes:
            No external access (network, disk, or database) is performed.

        """
        return iter(self.degrees)

    def __len__(self):
        """Return the number of degrees.

        Returns:
            int: The number of degrees in the list.

        Notes:
            No external access (network, disk, or database) is performed.

        """
        return len(self.degrees)

    def __getitem__(self, index: int):
        """Return the degree at the given index.

        Args:
            index (int): The index of the degree to retrieve.

        Returns:
            Degree: The Degree object at the specified index.

        Notes:
            No external access (network, disk, or database) is performed.

        """
        return self.degrees[index]


class Education(BaseModel):
    """Represents the educational background section of a resume.

    Attributes:
        degrees (Degrees | None): A Degrees object containing educational achievements, or None if no degrees.

    """

    degrees: Degrees | None = None
