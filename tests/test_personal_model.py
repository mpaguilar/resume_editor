import pytest
from pydantic import ValidationError

from resume_editor.app.models.resume.personal import (
    Banner,
    ContactInfo,
    Note,
    Personal,
    VisaStatus,
    Websites,
)


class TestPersonalModels:
    """Test cases for personal information models."""

    def test_contact_info_creation(self):
        """Test ContactInfo model creation."""
        contact = ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            location="New York, NY",
        )
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.phone == "123-456-7890"
        assert contact.location == "New York, NY"

    def test_contact_info_validation(self):
        """Test ContactInfo validation."""
        # Test name validation
        with pytest.raises(ValidationError, match="name must not be empty"):
            ContactInfo(name="", email="test@example.com")

        with pytest.raises(ValidationError, match="name must be a string"):
            ContactInfo(name=123, email="test@example.com")

        # Test optional fields can be None
        contact = ContactInfo(name="John Doe", email=None, phone=None, location=None)
        assert contact.name == "John Doe"
        assert contact.email is None
        assert contact.phone is None
        assert contact.location is None

    def test_contact_info_invalid_fields(self):
        """Test invalid field values for ContactInfo."""
        with pytest.raises(ValidationError, match="email must be a string or None"):
            ContactInfo(name="test", email=123)

        with pytest.raises(ValidationError, match="email must not be empty"):
            ContactInfo(name="test", email=" ")

        with pytest.raises(ValidationError, match="phone must be a string or None"):
            ContactInfo(name="test", phone=123)

        with pytest.raises(ValidationError, match="phone must not be empty"):
            ContactInfo(name="test", phone=" ")

        with pytest.raises(ValidationError, match="location must be a string or None"):
            ContactInfo(name="test", location=123)

        with pytest.raises(ValidationError, match="location must not be empty"):
            ContactInfo(name="test", location=" ")

    def test_websites_creation(self):
        """Test Websites model creation."""
        websites = Websites(
            website="https://johndoe.com",
            github="https://github.com/johndoe",
            linkedin="https://linkedin.com/in/johndoe",
            twitter="https://twitter.com/johndoe",
        )
        assert websites.website == "https://johndoe.com"
        assert websites.github == "https://github.com/johndoe"
        assert websites.linkedin == "https://linkedin.com/in/johndoe"
        assert websites.twitter == "https://twitter.com/johndoe"

    def test_websites_creation_with_defaults(self):
        """Test Websites model creation with default values."""
        websites = Websites()
        assert websites.website is None
        assert websites.github is None
        assert websites.linkedin is None
        assert websites.twitter is None

    def test_websites_creation_with_none_values(self):
        """Test Websites model creation with explicit None values."""
        websites = Websites(website=None, github=None, linkedin=None, twitter=None)
        assert websites.website is None
        assert websites.github is None
        assert websites.linkedin is None
        assert websites.twitter is None

    def test_websites_invalid_fields(self):
        """Test invalid field values for Websites."""
        with pytest.raises(ValidationError, match="website must be a string or None"):
            Websites(website=123)
        with pytest.raises(ValidationError, match="website must not be empty"):
            Websites(website=" ")

        with pytest.raises(ValidationError, match="github must be a string or None"):
            Websites(github=123)
        with pytest.raises(ValidationError, match="github must not be empty"):
            Websites(github=" ")

        with pytest.raises(ValidationError, match="linkedin must be a string or None"):
            Websites(linkedin=123)
        with pytest.raises(ValidationError, match="linkedin must not be empty"):
            Websites(linkedin=" ")

        with pytest.raises(ValidationError, match="twitter must be a string or None"):
            Websites(twitter=123)
        with pytest.raises(ValidationError, match="twitter must not be empty"):
            Websites(twitter=" ")

    def test_visa_status_creation(self):
        """Test VisaStatus model creation."""
        visa = VisaStatus(work_authorization="US Citizen", require_sponsorship=True)
        assert visa.work_authorization == "US Citizen"
        assert visa.require_sponsorship is True

    def test_visa_status_string_conversion(self):
        """Test VisaStatus string to boolean conversion."""
        visa = VisaStatus(work_authorization="H-1B", require_sponsorship="yes")
        assert visa.require_sponsorship is True

        visa = VisaStatus(work_authorization="H-1B", require_sponsorship="no")
        assert visa.require_sponsorship is False

    def test_visa_status_creation_with_defaults(self):
        """Test VisaStatus model creation with default values."""
        visa = VisaStatus()
        assert visa.work_authorization is None
        assert visa.require_sponsorship is None

    def test_visa_status_creation_with_none_values(self):
        """Test VisaStatus creation with explicit None values."""
        visa = VisaStatus(work_authorization=None, require_sponsorship=None)
        assert visa.work_authorization is None
        assert visa.require_sponsorship is None

    def test_visa_status_validation(self):
        """Test validation for VisaStatus fields."""
        with pytest.raises(
            ValidationError,
            match="work_authorization must be a string or None",
        ):
            VisaStatus(work_authorization=123)

        with pytest.raises(
            ValidationError,
            match="work_authorization must not be empty",
        ):
            VisaStatus(work_authorization=" ")

        with pytest.raises(
            ValidationError,
            match="require_sponsorship string must be 'yes' or 'no'",
        ):
            VisaStatus(require_sponsorship="maybe")

        with pytest.raises(
            ValidationError,
            match="require_sponsorship must be a boolean, string, or None",
        ):
            VisaStatus(require_sponsorship=123)

    def test_banner_creation(self):
        """Test Banner model creation and text cleaning."""
        raw_text = "\n\n\nHello\n\nWorld\n\n\n"
        banner = Banner(text=raw_text)
        assert banner.text == "Hello\nWorld"

    def test_banner_invalid_type(self):
        """Test Banner with invalid text type."""
        with pytest.raises(ValidationError, match="text must be a string"):
            Banner(text=123)

    def test_note_creation(self):
        """Test Note model creation and text cleaning."""
        raw_text = "\n\n\nImportant\n\nNote\n\n\n"
        note = Note(text=raw_text)
        assert note.text == "Important\nNote"

    def test_note_invalid_type(self):
        """Test Note with invalid text type."""
        with pytest.raises(ValidationError, match="text must be a string"):
            Note(text=123)

    def test_personal_creation(self):
        """Test Personal model creation."""
        contact = ContactInfo(name="John Doe", email="john@example.com")
        websites = Websites(github="https://github.com/johndoe")
        personal = Personal(contact_info=contact, websites=websites)
        assert personal.contact_info == contact
        assert personal.websites == websites
