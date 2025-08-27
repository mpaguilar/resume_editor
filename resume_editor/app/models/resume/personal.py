import logging

from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


class ContactInfo(BaseModel):
    """Holds personal contact details such as name, email, phone, and location.

    Attributes:
        name (str): The full name of the person.
        email (str | None): The email address of the person, or None if not provided.
        phone (str | None): The phone number of the person, or None if not provided.
        location (str | None): The physical location (e.g., city and country) of the person, or None if not provided.

    """

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v):
        """Validate the name field.

        Args:
            v: The name value to validate. Must be a non-empty string.

        Returns:
            str: The validated name (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the name is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure name is a string.
            2. Ensure name is not empty after stripping whitespace.

        """
        if not isinstance(v, str):
            raise ValueError("name must be a string")
        if not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        """Validate the email field.

        Args:
            v: The email value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated email (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the email is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure email is a string or None.
            2. Ensure email is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("email must be a string or None")
        if not v.strip():
            raise ValueError("email must not be empty")
        return v.strip()

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        """Validate the phone field.

        Args:
            v: The phone value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated phone (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the phone is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure phone is a string or None.
            2. Ensure phone is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("phone must be a string or None")
        if not v.strip():
            raise ValueError("phone must not be empty")
        return v.strip()

    @field_validator("location", mode="before")
    @classmethod
    def validate_location(cls, v):
        """Validate the location field.

        Args:
            v: The location value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated location (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the location is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure location is a string or None.
            2. Ensure location is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("location must be a string or None")
        if not v.strip():
            raise ValueError("location must not be empty")
        return v.strip()


class Websites(BaseModel):
    """Holds personal website and social media links.

    Attributes:
        website (str | None): The personal website URL, or None if not provided.
        github (str | None): The GitHub profile URL, or None if not provided.
        linkedin (str | None): The LinkedIn profile URL, or None if not provided.
        twitter (str | None): The Twitter profile URL, or None if not provided.

    """

    website: str | None = None
    github: str | None = None
    linkedin: str | None = None
    twitter: str | None = None

    @field_validator("website", mode="before")
    @classmethod
    def validate_website(cls, v):
        """Validate the website field.

        Args:
            v: The website value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated website (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the website is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure website is a string or None.
            2. Ensure website is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("website must be a string or None")
        if not v.strip():
            raise ValueError("website must not be empty")
        return v.strip()

    @field_validator("github", mode="before")
    @classmethod
    def validate_github(cls, v):
        """Validate the github field.

        Args:
            v: The github value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated github (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the github is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure github is a string or None.
            2. Ensure github is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("github must be a string or None")
        if not v.strip():
            raise ValueError("github must not be empty")
        return v.strip()

    @field_validator("linkedin", mode="before")
    @classmethod
    def validate_linkedin(cls, v):
        """Validate the linkedin field.

        Args:
            v: The linkedin value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated linkedin (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the linkedin is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure linkedin is a string or None.
            2. Ensure linkedin is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("linkedin must be a string or None")
        if not v.strip():
            raise ValueError("linkedin must not be empty")
        return v.strip()

    @field_validator("twitter", mode="before")
    @classmethod
    def validate_twitter(cls, v):
        """Validate the twitter field.

        Args:
            v: The twitter value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated twitter (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the twitter is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure twitter is a string or None.
            2. Ensure twitter is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("twitter must be a string or None")
        if not v.strip():
            raise ValueError("twitter must not be empty")
        return v.strip()


class VisaStatus(BaseModel):
    """Holds information about work authorization and sponsorship requirements.

    Attributes:
        work_authorization (str | None): The current work authorization status (e.g., "US Citizen", "H-1B"), or None if not provided.
        require_sponsorship (bool | None): A boolean indicating if sponsorship is required, or None if not provided.

    """

    work_authorization: str | None = None
    require_sponsorship: bool | None = None

    @field_validator("work_authorization", mode="before")
    @classmethod
    def validate_work_authorization(cls, v):
        """Validate the work_authorization field.

        Args:
            v: The work_authorization value to validate. Must be a non-empty string or None.

        Returns:
            str: The validated work_authorization (stripped of leading/trailing whitespace).

        Raises:
            ValueError: If the work_authorization is not a string or is empty after stripping whitespace.

        Notes:
            1. Ensure work_authorization is a string or None.
            2. Ensure work_authorization is not empty after stripping whitespace.

        """
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("work_authorization must be a string or None")
        if not v.strip():
            raise ValueError("work_authorization must not be empty")
        return v.strip()

    @field_validator("require_sponsorship", mode="before")
    @classmethod
    def validate_require_sponsorship(cls, v):
        """Validate the require_sponsorship field.

        Args:
            v: The require_sponsorship value to validate. Must be a boolean, string ("yes"/"no"), or None.

        Returns:
            bool: The validated require_sponsorship value.

        Raises:
            ValueError: If the require_sponsorship is not a boolean, string, or None, or if the string is not "yes" or "no".

        Notes:
            1. Ensure require_sponsorship is a boolean, string ("yes"/"no"), or None.
            2. If require_sponsorship is a string, convert "yes" to True and "no" to False.
            3. If require_sponsorship is not None and not a string, assign it directly.
            4. Otherwise, set require_sponsorship to None.

        """
        if v is None:
            return v
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            if v.lower() == "yes":
                return True
            elif v.lower() == "no":
                return False
            else:
                raise ValueError("require_sponsorship string must be 'yes' or 'no'")
        raise ValueError("require_sponsorship must be a boolean, string, or None")


class Banner(BaseModel):
    """Holds a personal banner message with cleaned text content.

    Attributes:
        text (str): The cleaned text content of the banner, with leading/trailing and internal blank lines removed.

    """

    text: str

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, v):
        """Validate the text field and clean it.

        Args:
            v: The raw text content of the banner, potentially including leading/trailing or internal blank lines.

        Returns:
            str: The cleaned text content of the banner.

        Raises:
            ValueError: If the text is not a string.

        Notes:
            1. Ensure text is a string.
            2. Split the input text into lines.
            3. Remove leading blank lines.
            4. Remove trailing blank lines.
            5. Filter out any lines that are blank after stripping whitespace.
            6. Join the remaining lines back into a single string.

        """
        if not isinstance(v, str):
            raise ValueError("text must be a string")

        # Split into lines
        lines = v.splitlines()

        # Remove leading blank lines
        while lines and not lines[0].strip():
            lines.pop(0)

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Filter out blank lines
        cleaned_lines = [line for line in lines if line.strip()]

        # Join back into a single string
        return "\n".join(cleaned_lines)


class Note(BaseModel):
    """Holds a personal note with cleaned text content.

    Attributes:
        text (str): The cleaned text content of the note, with leading/trailing and internal blank lines removed.

    """

    text: str

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, v):
        """Validate the text field and clean it.

        Args:
            v: The raw text content of the note, potentially including leading/trailing or internal blank lines.

        Returns:
            str: The cleaned text content of the note.

        Raises:
            ValueError: If the text is not a string.

        Notes:
            1. Ensure text is a string.
            2. Split the input text into lines.
            3. Remove leading blank lines.
            4. Remove trailing blank lines.
            5. Filter out any lines that are blank after stripping whitespace.
            6. Join the remaining lines back into a single string.

        """
        if not isinstance(v, str):
            raise ValueError("text must be a string")

        # Split into lines
        lines = v.splitlines()

        # Remove leading blank lines
        while lines and not lines[0].strip():
            lines.pop(0)

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Filter out blank lines
        cleaned_lines = [line for line in lines if line.strip()]

        # Join back into a single string
        return "\n".join(cleaned_lines)


class Personal(BaseModel):
    """Holds all personal information including contact details, websites, visa status, banner, and note.

    Attributes:
        contact_info (ContactInfo | None): An instance of ContactInfo containing personal contact details, or None if not provided.
        websites (Websites | None): An instance of Websites containing personal website links, or None if not provided.
        visa_status (VisaStatus | None): An instance of VisaStatus containing visa and sponsorship information, or None if not provided.
        banner (Banner | None): An instance of Banner containing a personal banner message, or None if not provided.
        note (Note | None): An instance of Note containing a personal note, or None if not provided.

    """

    contact_info: ContactInfo | None = None
    websites: Websites | None = None
    visa_status: VisaStatus | None = None
    banner: Banner | None = None
    note: Note | None = None
