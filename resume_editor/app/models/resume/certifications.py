import logging
from datetime import datetime

from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


class Certification(BaseModel):
    """Represents a professional certification.

    Attributes:
        name (str): The name of the certification.
        issuer (str | None): The organization that issued the certification.
        issued (datetime | None): The date the certification was issued.
        expires (datetime | None): The date the certification expires.
        certification_id (str | None): An identifier for the certification.

    """

    name: str
    issuer: str | None = None
    issued: datetime | None = None
    expires: datetime | None = None
    certification_id: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate the name field.

        Args:
            v: The name value to validate. Must be a non-empty string.

        Returns:
            str: The validated name.

        Notes:
            1. Ensure name is a string.
            2. Ensure name is not empty.

        """
        if not isinstance(v, str):
            raise ValueError("name must be a string")
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("issuer", "certification_id")
    @classmethod
    def validate_optional_strings(cls, v):
        """Validate optional string fields.

        Args:
            v: The field value to validate. Must be a string or None.

        Returns:
            str: The validated field value.

        Notes:
            1. Ensure field is a string or None.

        """
        if v is not None and not isinstance(v, str):
            raise ValueError("field must be a string or None")
        return v

    @field_validator("issued", "expires")
    @classmethod
    def validate_dates(cls, v):
        """Validate the date fields.

        Args:
            v: The date value to validate. Must be a datetime object or None.

        Returns:
            datetime: The validated date.

        Notes:
            1. Ensure date is a datetime object or None.

        """
        if v is not None and not isinstance(v, datetime):
            raise ValueError("date must be a datetime object or None")
        return v

    @field_validator("expires")
    @classmethod
    def validate_date_order(cls, v, info):
        """Validate that issued date is not after expires date.

        Args:
            v: The expires date value to validate.
            info: Validation info containing data.

        Returns:
            datetime: The validated expires date.

        Notes:
            1. If both issued and expires dates are provided, ensure issued is not after expires.

        """
        if v is not None:
            issued = info.data.get("issued")
            if issued is not None and v < issued:
                raise ValueError("expires date must not be before issued date")
        return v


class Certifications(BaseModel):
    """Represents a collection of professional certifications.

    Attributes:
        certifications (list[Certification]): A list of Certification objects.

    """

    certifications: list[Certification] = []

    @field_validator("certifications")
    @classmethod
    def validate_certifications(cls, v):
        """Validate the certifications field.

        Args:
            v: The certifications value to validate. Must be a list of Certification objects.

        Returns:
            list[Certification]: The validated certifications list.

        Notes:
            1. Ensure certifications is a list.
            2. Ensure all items in certifications are instances of Certification.

        """
        if not isinstance(v, list):
            raise ValueError("certifications must be a list")
        for item in v:
            if not isinstance(item, Certification):
                raise ValueError(
                    "all items in certifications must be Certification instances",
                )
        return v

    def __iter__(self):
        """Iterate over the certifications.

        Returns:
            An iterator over the list of certification objects.

        Notes:
            1. Return an iterator over the certifications list.

        """
        return iter(self.certifications)

    def __len__(self):
        """Return the number of certifications.

        Returns:
            The integer count of certifications in the list.

        Notes:
            1. Return the length of the certifications list.

        """
        return len(self.certifications)

    def __getitem__(self, index):
        """Return the certification at the given index.

        Args:
            index: The index of the certification to retrieve.

        Returns:
            The Certification object at the specified index.

        Notes:
            1. Retrieve and return the certification at the given index.

        """
        return self.certifications[index]

    @property
    def list_class(self):
        """Return the type that will be contained in the list.

        Returns:
            The Certification class.

        Notes:
            1. Return the Certification class.

        """
        return Certification
