from datetime import datetime

import pytest

from resume_editor.app.models.resume.certifications import Certification, Certifications
from resume_editor.app.models.resume.education import Degree, Degrees, Education
from resume_editor.app.models.resume.experience import (
    Experience,
)
from resume_editor.app.models.resume.personal import (
    ContactInfo,
    Personal,
)
from resume_editor.app.models.resume.resume import Resume


class TestEducationModels:
    """Test cases for education models."""

    def test_degree_creation(self):
        """Test Degree model creation."""
        start_date = datetime(2015, 9, 1)
        end_date = datetime(2019, 5, 1)
        degree = Degree(
            school="University of Example",
            degree="Bachelor of Science",
            start_date=start_date,
            end_date=end_date,
            major="Computer Science",
            gpa="3.8",
        )
        assert degree.school == "University of Example"
        assert degree.degree == "Bachelor of Science"
        assert degree.start_date == start_date
        assert degree.end_date == end_date
        assert degree.major == "Computer Science"
        assert degree.gpa == "3.8"

    def test_degree_date_validation(self):
        """Test Degree date validation."""
        start_date = datetime(2015, 9, 1)
        end_date = datetime(2010, 5, 1)  # Before start date

        with pytest.raises(ValueError):
            Degree(
                school="University of Example",
                start_date=start_date,
                end_date=end_date,
            )

    def test_degrees_collection(self):
        """Test Degrees collection."""
        degree1 = Degree(school="University 1", degree="BS")
        degree2 = Degree(school="University 2", degree="MS")
        degrees = Degrees(degrees=[degree1, degree2])

        assert len(degrees) == 2
        assert degrees[0] == degree1
        assert degrees[1] == degree2

        # Test iteration
        count = 0
        for degree in degrees:
            count += 1
        assert count == 2

    def test_education_creation(self):
        """Test Education model creation."""
        degree = Degree(school="University of Example", degree="BS")
        degrees = Degrees(degrees=[degree])
        education = Education(degrees=degrees)
        assert education.degrees == degrees


class TestCertificationModels:
    """Test cases for certification models."""

    def test_certification_creation(self):
        """Test Certification model creation."""
        issued = datetime(2020, 1, 1)
        expires = datetime(2023, 1, 1)
        cert = Certification(
            name="AWS Certified Developer",
            issuer="Amazon",
            issued=issued,
            expires=expires,
            certification_id="ABC123",
        )
        assert cert.name == "AWS Certified Developer"
        assert cert.issuer == "Amazon"
        assert cert.issued == issued
        assert cert.expires == expires
        assert cert.certification_id == "ABC123"

    def test_certification_date_validation(self):
        """Test Certification date validation."""
        issued = datetime(2020, 1, 1)
        expires = datetime(2019, 1, 1)  # Before issued date

        with pytest.raises(ValueError):
            Certification(name="Certified Professional", issued=issued, expires=expires)

    def test_certifications_collection(self):
        """Test Certifications collection."""
        cert1 = Certification(name="Cert 1")
        cert2 = Certification(name="Cert 2")
        certs = Certifications(certifications=[cert1, cert2])

        assert len(certs) == 2
        assert certs[0] == cert1
        assert certs[1] == cert2

        # Test iteration
        count = 0
        for cert in certs:
            count += 1
        assert count == 2


class TestResumeModel:
    """Test cases for the Resume model."""

    def test_resume_creation(self):
        """Test Resume model creation."""
        personal = Personal(contact_info=ContactInfo(name="John Doe"))
        education = Education()
        experience = Experience()
        certifications = Certifications()

        resume = Resume(
            personal=personal,
            education=education,
            experience=experience,
            certifications=certifications,
        )

        assert resume.personal == personal
        assert resume.education == education
        assert resume.experience == experience
        assert resume.certifications == certifications

    def test_resume_partial_creation(self):
        """Test Resume model creation with partial data."""
        personal = Personal(contact_info=ContactInfo(name="John Doe"))
        resume = Resume(personal=personal)

        assert resume.personal == personal
        assert resume.education is None
        assert resume.experience is None
        assert resume.certifications is None
