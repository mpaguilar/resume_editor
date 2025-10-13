import textwrap
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from resume_editor.app.api.routes.route_logic.resume_serialization_helpers import (
    _add_banner_markdown,
    _add_contact_info_markdown,
    _add_note_markdown,
    _add_project_description_markdown,
    _add_project_overview_markdown,
    _add_project_skills_markdown,
    _add_visa_status_markdown,
    _add_websites_markdown,
    _check_for_unparsed_content,
    _convert_writer_project_to_dict,
    _convert_writer_role_to_dict,
    _extract_data_from_personal_section,
    _parse_resume,
)
from resume_editor.app.api.routes.route_models import PersonalInfoResponse
from resume_editor.app.models.resume.experience import InclusionStatus


@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization_helpers.WriterResume.parse"
)
def test_parse_resume_success(mock_parse):
    """Test _parse_resume successfully parses content."""
    mock_resume = Mock()
    mock_parse.return_value = mock_resume

    result = _parse_resume("some content")

    assert result is mock_resume
    mock_parse.assert_called_once()


@patch(
    "resume_editor.app.api.routes.route_logic.resume_serialization_helpers.WriterResume.parse",
    side_effect=Exception("parse error"),
)
def test_parse_resume_failure(mock_parse):
    """Test _parse_resume raises ValueError on parsing failure."""
    with pytest.raises(ValueError, match="Failed to parse resume content."):
        _parse_resume("invalid content")

    mock_parse.assert_called_once()


class TestCheckForUnparsedContent:
    @pytest.mark.parametrize("section_name", ["personal", "experience", "education"])
    def test_parsed_section_exists(self, section_name):
        """Test it returns if parsed_section is provided."""
        _check_for_unparsed_content("content", section_name, Mock())
        # No exception raised

    @pytest.mark.parametrize("section_name", ["personal", "experience", "education"])
    def test_no_section_in_content(self, section_name):
        """Test it returns if the section is not in the content."""
        _check_for_unparsed_content("some random text", section_name, None)
        # No exception raised

    @pytest.mark.parametrize("section_name", ["personal", "experience", "education"])
    def test_empty_section(self, section_name):
        """Test it handles an empty section correctly."""
        content = f"# {section_name.capitalize()}\n\n# Another Section"
        _check_for_unparsed_content(content, section_name, None)
        # No exception raised

    @pytest.mark.parametrize("section_name", ["personal", "experience", "education"])
    def test_unparsed_subheader_raises_error(self, section_name):
        """Test it raises ValueError when unparsed content is a subheader."""
        content = textwrap.dedent(
            f"""
            # {section_name.capitalize()}
            ## Some subheader
            # Another Section
            """
        )
        with pytest.raises(
            ValueError, match=f"Failed to parse {section_name} info from resume content."
        ):
            _check_for_unparsed_content(content, section_name, None)

    @pytest.mark.parametrize("section_name", ["personal", "experience", "education"])
    def test_unparsed_content_raises_error(self, section_name):
        """Test it raises ValueError if unparsed content is found."""
        content = textwrap.dedent(
            f"""
            # {section_name.capitalize()}
            This is unparsed content.
            # Another Section
        """
        )
        with pytest.raises(
            ValueError, match=f"Failed to parse {section_name} info from resume content."
        ):
            _check_for_unparsed_content(content, section_name, None)


class TestExtractDataFromPersonalSection:
    def test_no_personal_section(self):
        """Test it returns an empty dict if personal section is None."""
        assert _extract_data_from_personal_section(None) == {}

    def test_full_personal_data(self):
        """Test it extracts all fields correctly."""
        mock_personal = Mock()
        mock_personal.contact_info.name = "John Doe"
        mock_personal.contact_info.email = "john@example.com"
        mock_personal.contact_info.phone = "123-456-7890"
        mock_personal.contact_info.location = "Some City"
        mock_personal.websites.website = "example.com"
        mock_personal.websites.github = "johndoe"
        mock_personal.websites.linkedin = "johndoe-li"
        mock_personal.websites.twitter = "@johndoe"
        mock_personal.visa_status.work_authorization = "Citizen"
        mock_personal.visa_status.require_sponsorship = True
        mock_personal.banner.text = "A banner"
        mock_personal.note.text = "A note"

        data = _extract_data_from_personal_section(mock_personal)

        expected_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "location": "Some City",
            "website": "example.com",
            "github": "johndoe",
            "linkedin": "johndoe-li",
            "twitter": "@johndoe",
            "work_authorization": "Citizen",
            "require_sponsorship": True,
            "banner": "A banner",
            "note": "A note",
        }
        assert data == expected_data

    def test_partial_personal_data(self):
        """Test it handles partially missing data."""
        mock_personal = Mock()
        mock_personal.contact_info.name = "John Doe"
        mock_personal.contact_info.email = None
        mock_personal.contact_info.phone = None
        mock_personal.contact_info.location = None
        mock_personal.websites = None
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        data = _extract_data_from_personal_section(mock_personal)

        assert data == {"name": "John Doe", "email": None, "phone": None, "location": None}

    def test_empty_personal_data(self):
        """Test it returns an empty dict if no data is present."""
        mock_personal = Mock()
        mock_personal.contact_info = None
        mock_personal.websites = None
        mock_personal.visa_status = None
        mock_personal.banner = None
        mock_personal.note = None

        data = _extract_data_from_personal_section(mock_personal)
        assert data == {}


class TestConvertWriterRoleToDict:
    def test_full_role_data(self):
        """Test it converts a role with all fields."""
        mock_role = Mock()
        mock_role.basics.company = "Test Corp"
        mock_role.basics.title = "Dev"
        mock_role.basics.start_date = datetime(2020, 1, 1)
        mock_role.basics.end_date = datetime(2021, 1, 1)
        mock_role.basics.location = "Remote"
        mock_role.basics.agency_name = "Agency"
        mock_role.basics.job_category = "Cat"
        mock_role.basics.employment_type = "Full"
        mock_role.basics.reason_for_change = "Reason"
        mock_role.summary.summary = "A summary"
        mock_role.responsibilities.text = "Some duties"
        mock_role.skills.skills = ["python", "docker"]

        result = _convert_writer_role_to_dict(mock_role)

        assert result["basics"]["company"] == "Test Corp"
        assert result["basics"]["title"] == "Dev"
        assert result["summary"]["text"] == "A summary"
        assert result["responsibilities"]["text"] == "Some duties"
        assert result["skills"]["skills"] == ["python", "docker"]

    def test_partial_role_data(self):
        """Test it converts a role with some fields missing."""
        mock_role = Mock()
        mock_role.basics.company = "Test Corp"
        mock_role.basics.title = "Dev"
        mock_role.basics.start_date = datetime(2020, 1, 1)
        mock_role.basics.end_date = None
        mock_role.basics.location = None
        mock_role.basics.agency_name = None
        mock_role.basics.job_category = None
        mock_role.basics.employment_type = None
        mock_role.basics.reason_for_change = None
        mock_role.summary = None
        mock_role.responsibilities = None
        mock_role.skills = None

        result = _convert_writer_role_to_dict(mock_role)

        assert "summary" not in result
        assert "responsibilities" not in result
        assert "skills" not in result
        assert result["basics"]["company"] == "Test Corp"

    def test_empty_role_data(self):
        """Test it returns an empty dict for an empty role."""
        mock_role = Mock()
        mock_role.basics = None
        mock_role.summary = None
        mock_role.responsibilities = None
        mock_role.skills = None

        result = _convert_writer_role_to_dict(mock_role)

        assert result == {}


class TestConvertWriterProjectToDict:
    def test_full_project_data(self):
        """Test it converts a project with all fields."""
        mock_project = Mock()
        mock_project.overview.title = "A Project"
        mock_project.overview.url = "http://example.com"
        mock_project.overview.url_description = "A link"
        mock_project.overview.start_date = datetime(2020, 1, 1)
        mock_project.overview.end_date = datetime(2021, 1, 1)
        mock_project.overview.inclusion_status = InclusionStatus.NOT_RELEVANT
        mock_project.description.text = "A description"
        mock_project.skills.skills = ["api", "htmx"]

        result = _convert_writer_project_to_dict(mock_project)

        assert result["overview"]["title"] == "A Project"
        assert result["overview"]["url"] == "http://example.com"
        assert result["overview"]["inclusion_status"] == InclusionStatus.NOT_RELEVANT
        assert result["description"]["text"] == "A description"
        assert result["skills"]["skills"] == ["api", "htmx"]

    def test_partial_project_data_defaults_inclusion_status(self):
        """Test it converts a project with some fields missing and defaults inclusion."""
        mock_project = Mock()
        # use spec to avoid inclusion_status being on the mock
        mock_overview = Mock(
            spec=["title", "url", "url_description", "start_date", "end_date"]
        )
        mock_overview.title = "A Project"
        mock_overview.url = None
        mock_overview.url_description = None
        mock_overview.start_date = datetime(2020, 1, 1)
        mock_overview.end_date = None
        mock_project.overview = mock_overview
        mock_project.description = None
        mock_project.skills = None

        result = _convert_writer_project_to_dict(mock_project)

        assert "description" not in result
        assert "skills" not in result
        assert result["overview"]["title"] == "A Project"
        assert result["overview"]["inclusion_status"] == InclusionStatus.INCLUDE

    def test_empty_project_data(self):
        """Test it returns an empty dict for an empty project."""
        mock_project = Mock()
        mock_project.overview = None
        mock_project.description = None
        mock_project.skills = None

        result = _convert_writer_project_to_dict(mock_project)

        assert result == {}


class TestAddContactInfoMarkdown:
    def test_with_full_info(self):
        personal_info = PersonalInfoResponse(
            name="John Doe",
            email="john@example.com",
            phone="123-456-7890",
            location="City, State",
        )
        lines = []
        _add_contact_info_markdown(personal_info, lines)
        expected = [
            "## Contact Information",
            "",
            "Name: John Doe",
            "Email: john@example.com",
            "Phone: 123-456-7890",
            "Location: City, State",
            "",
        ]
        assert lines == expected

    def test_with_partial_info(self):
        personal_info = PersonalInfoResponse(name="John Doe")
        lines = []
        _add_contact_info_markdown(personal_info, lines)
        expected = ["## Contact Information", "", "Name: John Doe", ""]
        assert lines == expected

    def test_with_no_info(self):
        personal_info = PersonalInfoResponse()
        lines = []
        _add_contact_info_markdown(personal_info, lines)
        assert lines == []


class TestAddWebsitesMarkdown:
    def test_with_full_info(self):
        personal_info = PersonalInfoResponse(
            github="johndoe",
            linkedin="johndoe-li",
            website="example.com",
            twitter="@johndoe",
        )
        lines = []
        _add_websites_markdown(personal_info, lines)
        expected = [
            "## Websites",
            "",
            "GitHub: johndoe",
            "LinkedIn: johndoe-li",
            "Website: example.com",
            "Twitter: @johndoe",
            "",
        ]
        assert lines == expected

    def test_with_partial_info(self):
        personal_info = PersonalInfoResponse(github="johndoe")
        lines = []
        _add_websites_markdown(personal_info, lines)
        expected = ["## Websites", "", "GitHub: johndoe", ""]
        assert lines == expected

    def test_with_no_info(self):
        personal_info = PersonalInfoResponse()
        lines = []
        _add_websites_markdown(personal_info, lines)
        assert lines == []


class TestAddVisaStatusMarkdown:
    def test_with_full_info(self):
        personal_info = PersonalInfoResponse(
            work_authorization="US Citizen", require_sponsorship=False
        )
        lines = []
        _add_visa_status_markdown(personal_info, lines)
        expected = [
            "## Visa Status",
            "",
            "Work Authorization: US Citizen",
            "Require sponsorship: No",
            "",
        ]
        assert lines == expected

    def test_with_auth_only(self):
        personal_info = PersonalInfoResponse(work_authorization="US Citizen")
        lines = []
        _add_visa_status_markdown(personal_info, lines)
        expected = ["## Visa Status", "", "Work Authorization: US Citizen", ""]
        assert lines == expected

    def test_with_sponsorship_true_only(self):
        personal_info = PersonalInfoResponse(require_sponsorship=True)
        lines = []
        _add_visa_status_markdown(personal_info, lines)
        expected = ["## Visa Status", "", "Require sponsorship: Yes", ""]
        assert lines == expected

    def test_with_sponsorship_false_only(self):
        personal_info = PersonalInfoResponse(require_sponsorship=False)
        lines = []
        _add_visa_status_markdown(personal_info, lines)
        expected = ["## Visa Status", "", "Require sponsorship: No", ""]
        assert lines == expected

    def test_with_no_info(self):
        personal_info = PersonalInfoResponse()
        lines = []
        _add_visa_status_markdown(personal_info, lines)
        assert lines == []


class TestAddBannerMarkdown:
    def test_with_banner(self):
        personal_info = PersonalInfoResponse(banner="Some banner text")
        lines = []
        _add_banner_markdown(personal_info, lines)
        expected = ["## Banner", "", "Some banner text", ""]
        assert lines == expected

    def test_with_no_banner(self):
        personal_info = PersonalInfoResponse()
        lines = []
        _add_banner_markdown(personal_info, lines)
        assert lines == []


class TestAddNoteMarkdown:
    def test_with_note(self):
        personal_info = PersonalInfoResponse(note="Some note text")
        lines = []
        _add_note_markdown(personal_info, lines)
        expected = ["## Note", "", "Some note text", ""]
        assert lines == expected

    def test_with_no_note(self):
        personal_info = PersonalInfoResponse()
        lines = []
        _add_note_markdown(personal_info, lines)
        assert lines == []


class TestAddProjectOverviewMarkdown:
    def test_with_full_info(self):
        overview = Mock(
            title="Project A",
            url="http://example.com",
            url_description="Link",
            start_date=datetime(2022, 1, 1),
            end_date=datetime(2022, 12, 31),
        )
        lines = []
        _add_project_overview_markdown(overview, lines)
        expected = [
            "#### Overview",
            "",
            "Title: Project A",
            "Url: http://example.com",
            "Url Description: Link",
            "Start date: 01/2022",
            "End date: 12/2022",
            "",
        ]
        assert lines == expected

    def test_with_partial_info(self):
        overview = Mock(
            title="Project B", url=None, url_description=None, start_date=None, end_date=None
        )
        lines = []
        _add_project_overview_markdown(overview, lines)
        expected = ["#### Overview", "", "Title: Project B", ""]
        assert lines == expected

    def test_with_no_info(self):
        overview = Mock(
            title=None, url=None, url_description=None, start_date=None, end_date=None
        )
        lines = []
        _add_project_overview_markdown(overview, lines)
        assert lines == []


class TestAddProjectDescriptionMarkdown:
    def test_with_description(self):
        description = Mock(text="A sample description.")
        lines = []
        _add_project_description_markdown(description, lines)
        expected = ["#### Description", "", "A sample description.", ""]
        assert lines == expected

    def test_with_no_description_object(self):
        lines = []
        _add_project_description_markdown(None, lines)
        assert lines == []

    def test_with_no_description_text(self):
        description = Mock(text=None)
        lines = []
        _add_project_description_markdown(description, lines)
        assert lines == []


class TestAddProjectSkillsMarkdown:
    def test_with_skills(self):
        skills = Mock(skills=["Python", "FastAPI"])
        lines = []
        _add_project_skills_markdown(skills, lines)
        expected = ["#### Skills", "", "* Python", "* FastAPI", ""]
        assert lines == expected

    def test_with_no_skills_object(self):
        lines = []
        _add_project_skills_markdown(None, lines)
        assert lines == []

    def test_with_empty_skills_list(self):
        skills = Mock(skills=[])
        lines = []
        _add_project_skills_markdown(skills, lines)
        assert lines == []
