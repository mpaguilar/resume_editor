from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization import (
    extract_certifications_info,
    serialize_certifications_to_markdown,
)
from resume_editor.app.api.routes.route_models import CertificationsResponse


def test_serialize_certifications_to_markdown_with_issuer():
    """Test serializing certifications to cover the 'issuer' field presence."""
    certifications = CertificationsResponse(
        certifications=[
            {"name": "Cert Name", "issuer": "Cert Issuer", "id": "123"},
        ],
    )
    markdown = serialize_certifications_to_markdown(certifications)
    assert "Issuer: Cert Issuer" in markdown
    assert "Certification ID: 123" in markdown


def test_serialize_certifications_to_markdown_with_data():
    """Test that certifications are serialized correctly to markdown."""
    # This covers the main serialization logic for certifications
    certifications_info = CertificationsResponse(
        certifications=[
            {
                "name": "Certified Pythonista",
                "issuer": "Python Institute",
                "id": "12345",
                "issued_date": "2023-01-15T00:00:00",
                "expiry_date": "2025-01-15T00:00:00",
            },
            {
                "name": "Certified FastAPI Developer",
                "issuer": None,
                "id": "67890",
                "issued_date": "2024-02-20T00:00:00",
                "expiry_date": None,
            },
        ],
    )
    expected_markdown = """# Certifications

## Certification

Name: Certified Pythonista
Issuer: Python Institute
Issued: 01/2023
Expires: 01/2025
Certification ID: 12345

## Certification

Name: Certified FastAPI Developer
Issued: 02/2024
Certification ID: 67890

"""
    result = serialize_certifications_to_markdown(certifications_info)
    assert result == expected_markdown


def test_serialize_certifications_to_markdown_no_data():
    """Test that an empty string is returned for no certifications."""
    # This covers the branch where there are no certifications to serialize
    certifications_info = CertificationsResponse(certifications=[])
    result = serialize_certifications_to_markdown(certifications_info)
    assert result == ""


def test_serialize_certifications_to_markdown_partial_fields():
    """Test serializing certifications with partial fields for coverage."""
    # Certification with name but no issuer
    mock_cert1 = Mock()
    mock_cert1.name = "Cert One"
    mock_cert1.issuer = None
    mock_cert1.issued = None
    mock_cert1.expires = None
    mock_cert1.certification_id = None

    # Certification with no name but with issuer
    mock_cert2 = Mock()
    mock_cert2.name = None
    mock_cert2.issuer = "Issuer Two"
    mock_cert2.issued = None
    mock_cert2.expires = None
    mock_cert2.certification_id = None

    mock_certs_response = Mock()
    mock_certs_response.certifications = [mock_cert1, mock_cert2]

    markdown = serialize_certifications_to_markdown(mock_certs_response)

    cert_sections = markdown.split("## Certification\n\n")
    cert1_markdown = cert_sections[1]
    assert "Name: Cert One" in cert1_markdown
    assert "Issuer: " not in cert1_markdown

    cert2_markdown = cert_sections[2]
    assert "Name: " not in cert2_markdown
    assert "Issuer: Issuer Two" in cert2_markdown


class TestExtractCertificationsInfo:
    """Test cases for certifications info extraction functions."""

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_certifications_info_no_certifications(self, mock_parse):
        """Test certifications extraction when certifications section is missing."""
        mock_resume = Mock()
        mock_resume.certifications = None
        mock_parse.return_value = mock_resume

        response = extract_certifications_info("any content")
        assert response.certifications == []

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
    )
    def test_extract_certifications_info_partial_data(self, mock_parse):
        """Test certifications extraction with partial data in a certification."""
        mock_cert = Mock()
        mock_cert.name = "Test Cert"
        mock_cert.issuer = None
        mock_cert.certification_id = "123"
        mock_cert.issued = None
        mock_cert.expires = None

        # The Certifications object is iterable
        mock_resume = Mock(certifications=[mock_cert])
        mock_parse.return_value = mock_resume

        response = extract_certifications_info("any content")
        assert len(response.certifications) == 1
        cert = response.certifications[0]
        assert cert.name == "Test Cert"
        assert cert.issuer is None
        assert cert.certification_id == "123"
        assert cert.issued is None
        assert cert.expires is None

    @patch(
        "resume_editor.app.api.routes.route_logic.resume_serialization.WriterResume.parse",
        side_effect=Exception("mock parse error"),
    )
    def test_extract_certifications_info_parse_fails(self, mock_parse):
        """Test certifications extraction when parsing fails."""
        with pytest.raises(ValueError, match="Failed to parse certifications info"):
            extract_certifications_info("invalid content")


def test_serialize_certifications_to_markdown_none_input():
    """Test serialize_certifications_to_markdown with None input."""
    result = serialize_certifications_to_markdown(None)
    assert result == ""


def test_serialize_certifications_to_markdown_partial_data():
    """Test serialization of partial certifications information to Markdown."""
    certifications = CertificationsResponse(
        certifications=[
            {
                "name": "Partial Certification",
                "issuer": None,
                "id": "PART-123",
                "issued_date": None,
                "expiry_date": "2025-12-31",
            },
        ],
    )
    markdown = serialize_certifications_to_markdown(certifications)
    expected = """# Certifications

## Certification

Name: Partial Certification
Expires: 12/2025
Certification ID: PART-123

"""
    assert markdown == expected
