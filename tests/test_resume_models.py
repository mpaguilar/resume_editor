from datetime import datetime

import pytest

from resume_editor.app.models.resume.certifications import Certification, Certifications
from resume_editor.app.models.resume.education import Degree, Degrees, Education
from resume_editor.app.models.resume.experience import (
    Experience,
    Project,
    ProjectDescription,
    ProjectOverview,
    Projects,
    Role,
    RoleBasics,
    Roles,
    RoleSkills,
    RoleSummary,
)
from resume_editor.app.models.resume.personal import (
    Banner,
    ContactInfo,
    Note,
    Personal,
    VisaStatus,
    Websites,
)
from resume_editor.app.models.resume.resume import Resume


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
        with pytest.raises(ValueError):
            ContactInfo(name="", email="test@example.com")

        with pytest.raises(ValueError):
            ContactInfo(name=123, email="test@example.com")

        # Test optional fields can be None
        contact = ContactInfo(name="John Doe", email=None, phone=None, location=None)
        assert contact.name == "John Doe"
        assert contact.email is None
        assert contact.phone is None
        assert contact.location is None

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

    def test_banner_creation(self):
        """Test Banner model creation and text cleaning."""
        raw_text = "\n\n\nHello\n\nWorld\n\n\n"
        banner = Banner(text=raw_text)
        assert banner.text == "Hello\nWorld"

    def test_note_creation(self):
        """Test Note model creation and text cleaning."""
        raw_text = "\n\n\nImportant\n\nNote\n\n\n"
        note = Note(text=raw_text)
        assert note.text == "Important\nNote"

    def test_personal_creation(self):
        """Test Personal model creation."""
        contact = ContactInfo(name="John Doe", email="john@example.com")
        websites = Websites(github="https://github.com/johndoe")
        personal = Personal(contact_info=contact, websites=websites)
        assert personal.contact_info == contact
        assert personal.websites == websites


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


class TestExperienceModels:
    """Test cases for experience models."""

    def test_role_basics_creation(self):
        """Test RoleBasics model creation."""
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2022, 12, 31)
        basics = RoleBasics(
            company="Tech Corp",
            start_date=start_date,
            end_date=end_date,
            title="Software Engineer",
        )
        assert basics.company == "Tech Corp"
        assert basics.start_date == start_date
        assert basics.end_date == end_date
        assert basics.title == "Software Engineer"

    def test_role_skills_creation(self):
        """Test RoleSkills model creation."""
        skills = RoleSkills(skills=["Python", "JavaScript", "SQL"])
        assert len(skills) == 3
        assert skills[0] == "Python"
        assert skills[1] == "JavaScript"
        assert skills[2] == "SQL"

    def test_role_skills_cleaning(self):
        """Test RoleSkills cleaning of input."""
        skills = RoleSkills(skills=[" Python ", "", "JavaScript ", "  ", "SQL"])
        assert len(skills) == 3
        assert skills[0] == "Python"
        assert skills[1] == "JavaScript"
        assert skills[2] == "SQL"

    def test_role_creation(self):
        """Test Role model creation."""
        basics = RoleBasics(
            company="Tech Corp",
            start_date=datetime(2020, 1, 1),
            title="Software Engineer",
        )
        summary = RoleSummary(summary="Developed web applications")
        role = Role(basics=basics, summary=summary)
        assert role.basics == basics
        assert role.summary == summary

    def test_roles_collection(self):
        """Test Roles collection."""
        role1 = Role(
            basics=RoleBasics(
                company="Company 1",
                start_date=datetime(2020, 1, 1),
                title="Engineer",
            ),
        )
        role2 = Role(
            basics=RoleBasics(
                company="Company 2",
                start_date=datetime(2021, 1, 1),
                title="Senior Engineer",
            ),
        )
        roles = Roles(roles=[role1, role2])

        assert len(roles) == 2
        assert roles[0] == role1
        assert roles[1] == role2

    def test_project_creation(self):
        """Test Project model creation."""
        overview = ProjectOverview(
            title="Web App",
            start_date=datetime(2021, 1, 1),
            end_date=datetime(2021, 6, 1),
        )
        description = ProjectDescription(text="A web application")
        project = Project(overview=overview, description=description)
        assert project.overview == overview
        assert project.description == description

    def test_projects_collection(self):
        """Test Projects collection."""
        project1 = Project(
            overview=ProjectOverview(title="Project 1"),
            description=ProjectDescription(text="Description 1"),
        )
        project2 = Project(
            overview=ProjectOverview(title="Project 2"),
            description=ProjectDescription(text="Description 2"),
        )
        projects = Projects(projects=[project1, project2])

        assert len(projects) == 2
        assert projects[0] == project1
        assert projects[1] == project2

    def test_experience_creation(self):
        """Test Experience model creation."""
        roles = Roles(roles=[])
        projects = Projects(projects=[])
        experience = Experience(roles=roles, projects=projects)
        assert experience.roles == roles
        assert experience.projects == projects


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
