"""Tests for the certifications models."""

from datetime import datetime

import pytest

from resume_editor.app.models.resume.certifications import Certification, Certifications


class TestCertification:
    """Test Certification model."""

    def test_certification_creation_valid(self):
        """Test creating a valid Certification."""
        cert = Certification(
            name="AWS Certified Solutions Architect",
            issuer="Amazon Web Services",
            issued=datetime(2023, 1, 15),
            expires=datetime(2026, 1, 15),
            certification_id="AWS123456",
        )
        assert cert.name == "AWS Certified Solutions Architect"
        assert cert.issuer == "Amazon Web Services"
        assert cert.issued == datetime(2023, 1, 15)
        assert cert.expires == datetime(2026, 1, 15)
        assert cert.certification_id == "AWS123456"

    def test_certification_creation_with_none_values(self):
        """Test creating a Certification with optional fields as None."""
        cert = Certification(
            name="Google Cloud Professional",
            issuer=None,
            issued=None,
            expires=None,
            certification_id=None,
        )
        assert cert.name == "Google Cloud Professional"
        assert cert.issuer is None
        assert cert.issued is None
        assert cert.expires is None
        assert cert.certification_id is None

    def test_certification_name_validation_empty_string(self):
        """Test Certification name validation with empty string."""
        with pytest.raises(ValueError, match="name must not be empty"):
            Certification(name="", issuer="Test Issuer")

    def test_certification_name_validation_whitespace_only(self):
        """Test Certification name validation with whitespace only."""
        with pytest.raises(ValueError, match="name must not be empty"):
            Certification(name="   ", issuer="Test Issuer")

    def test_certification_name_validation_invalid_type(self):
        """Test Certification name validation with invalid type."""
        # Test the specific line: if not isinstance(v, str): raise ValueError("name must be a string")
        with pytest.raises(ValueError, match="name must be a string"):
            Certification.validate_name(123)  # Should be string

    def test_certification_name_stripped(self):
        """Test that Certification name is stripped of whitespace."""
        cert = Certification(name="  AWS Certified  ", issuer="Amazon Web Services")
        assert cert.name == "AWS Certified"

    def test_certification_issuer_validation_invalid_type(self):
        """Test Certification issuer validation with invalid type."""
        # Test the specific line: if v is not None and not isinstance(v, str): raise ValueError("field must be a string or None")
        with pytest.raises(ValueError, match="field must be a string or None"):
            Certification.validate_optional_strings(123)  # Should be string or None

    def test_certification_certification_id_validation_invalid_type(self):
        """Test Certification certification_id validation with invalid type."""
        # Test the specific line: if v is not None and not isinstance(v, str): raise ValueError("field must be a string or None")
        with pytest.raises(ValueError, match="field must be a string or None"):
            Certification.validate_optional_strings(123)  # Should be string or None

    def test_certification_issued_validation_invalid_type(self):
        """Test Certification issued validation with invalid type."""
        # Test the specific line: if v is not None and not isinstance(v, datetime): raise ValueError("date must be a datetime object or None")
        with pytest.raises(ValueError, match="date must be a datetime object or None"):
            Certification.validate_dates("not a datetime")  # Should be datetime or None

    def test_certification_expires_validation_invalid_type(self):
        """Test Certification expires validation with invalid type."""
        # Test the specific line: if v is not None and not isinstance(v, datetime): raise ValueError("date must be a datetime object or None")
        with pytest.raises(ValueError, match="date must be a datetime object or None"):
            Certification.validate_dates("not a datetime")  # Should be datetime or None

    def test_certification_date_order_validation(self):
        """Test Certification date order validation."""
        with pytest.raises(
            ValueError,
            match="expires date must not be before issued date",
        ):
            Certification(
                name="Test Cert",
                issued=datetime(2023, 1, 15),
                expires=datetime(2022, 1, 15),  # Expires before issued
            )

    # Additional tests to improve coverage for missing lines
    def test_certification_issuer_none_valid(self):
        """Test Certification issuer with None value is valid."""
        cert = Certification(name="Test Cert", issuer=None)
        assert cert.issuer is None

    def test_certification_certification_id_none_valid(self):
        """Test Certification certification_id with None value is valid."""
        cert = Certification(name="Test Cert", certification_id=None)
        assert cert.certification_id is None

    def test_certification_issued_none_valid(self):
        """Test Certification issued with None value is valid."""
        cert = Certification(name="Test Cert", issued=None)
        assert cert.issued is None

    def test_certification_expires_none_valid(self):
        """Test Certification expires with None value is valid."""
        cert = Certification(name="Test Cert", expires=None)
        assert cert.expires is None

    def test_certification_valid_date_order_same_date(self):
        """Test Certification with same issued and expires dates is valid."""
        date = datetime(2023, 1, 15)
        cert = Certification(name="Test Cert", issued=date, expires=date)
        assert cert.issued == date
        assert cert.expires == date

    def test_certifications_creation_empty_list(self):
        """Test creating Certifications with empty list."""
        certs = Certifications()
        assert len(certs) == 0
        assert list(certs) == []

    def test_certifications_creation_with_list(self):
        """Test creating Certifications with a list of Certification objects."""
        cert1 = Certification(name="Cert 1", issuer="Issuer 1")
        cert2 = Certification(name="Cert 2", issuer="Issuer 2")
        certs = Certifications(certifications=[cert1, cert2])
        assert len(certs) == 2
        assert certs[0] == cert1
        assert certs[1] == cert2
        assert list(certs) == [cert1, cert2]

    def test_certifications_iteration(self):
        """Test iterating over Certifications."""
        cert1 = Certification(name="Cert 1", issuer="Issuer 1")
        cert2 = Certification(name="Cert 2", issuer="Issuer 2")
        certs = Certifications(certifications=[cert1, cert2])

        collected = []
        for cert in certs:
            collected.append(cert)

        assert collected == [cert1, cert2]

    def test_certifications_validation_invalid_type(self):
        """Test Certifications validation with invalid type."""
        # Test the specific lines: if not isinstance(v, list): raise ValueError("certifications must be a list")
        with pytest.raises(ValueError, match="certifications must be a list"):
            Certifications.validate_certifications("not a list")

    def test_certifications_validation_invalid_items(self):
        """Test Certifications validation with invalid items."""
        # Test the specific lines:
        # for item in v:
        #     if not isinstance(item, Certification):
        #         raise ValueError("all items in certifications must be Certification instances")
        with pytest.raises(
            ValueError,
            match="all items in certifications must be Certification instances",
        ):
            Certifications.validate_certifications(["not a certification object"])

    def test_certifications_list_class_property(self):
        """Test Certifications list_class property."""
        certs = Certifications()
        assert certs.list_class == Certification

    # Additional tests to improve coverage for missing lines
    def test_certifications_len_method(self):
        """Test Certifications __len__ method."""
        cert1 = Certification(name="Cert 1", issuer="Issuer 1")
        cert2 = Certification(name="Cert 2", issuer="Issuer 2")
        certs = Certifications(certifications=[cert1, cert2])
        assert len(certs) == 2

        empty_certs = Certifications()
        assert len(empty_certs) == 0

    def test_certifications_getitem_method(self):
        """Test Certifications __getitem__ method."""
        cert1 = Certification(name="Cert 1", issuer="Issuer 1")
        cert2 = Certification(name="Cert 2", issuer="Issuer 2")
        certs = Certifications(certifications=[cert1, cert2])

        assert certs[0] == cert1
        assert certs[1] == cert2

    def test_certifications_getitem_index_error(self):
        """Test Certifications __getitem__ method with invalid index."""
        certs = Certifications()
        with pytest.raises(IndexError):
            certs[0]
