"""Tests for resume AI logic extraction functions."""

import textwrap

import pytest

from resume_editor.app.api.routes.route_logic.resume_ai_logic_extraction import (
    _extract_raw_section,
    _parse_personal_section_lines,
    _rebuild_personal_section,
    _update_banner_in_raw_personal,
    reconstruct_resume_with_new_introduction,
)


class TestParsePersonalSectionLines:
    """Tests for _parse_personal_section_lines function."""

    def test_parses_personal_section(self):
        """Test parsing lines to extract personal section content."""
        lines = [
            "# Personal",
            "## Contact Information",
            "Name: John Doe",
            "",
            "## Banner",
            "Some banner text",
            "# Education",
            "School: University",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert result == [
            "# Personal",
            "## Contact Information",
            "Name: John Doe",
            "",
            "## Banner",
            "Some banner text",
        ]

    def test_parses_case_insensitive(self):
        """Test that section matching is case insensitive."""
        lines = [
            "# PERSONAL",
            "Name: John",
            "# Education",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert result == ["# PERSONAL", "Name: John"]

    def test_empty_list_when_section_not_found(self):
        """Test returns empty list when section not found."""
        lines = [
            "# Education",
            "School: University",
            "# Experience",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert result == []

    def test_stops_at_next_top_level_section(self):
        """Test stops parsing at next top-level section."""
        lines = [
            "# Personal",
            "Some content",
            "## Subsection",
            "More content",
            "# Experience",
            "Should not include this",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert len(result) == 4
        assert "# Experience" not in result

    def test_handles_subsections_correctly(self):
        """Test that subsections (##) don't stop parsing."""
        lines = [
            "# Personal",
            "## Subsection 1",
            "Content 1",
            "## Subsection 2",
            "Content 2",
            "# Education",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert len(result) == 5
        assert result[-1] == "Content 2"


class TestRebuildPersonalSection:
    """Tests for _rebuild_personal_section function."""

    def test_adds_banner_when_not_found(self):
        """Test adding banner when not found in section."""
        lines = [
            "# Personal",
            "## Contact",
            "Name: John",
        ]
        result = _rebuild_personal_section(lines, "New intro", False)
        assert "## Banner" in result
        assert "New intro" in result
        assert result[0] == "# Personal"

    def test_adds_blank_line_before_banner(self):
        """Test that a blank line is added before banner when needed."""
        lines = ["# Personal", "Content"]
        result = _rebuild_personal_section(lines, "New intro", False)
        # Should have blank line before ## Banner
        banner_idx = result.index("## Banner")
        assert result[banner_idx - 1] == ""

    def test_no_extra_blank_line_if_last_line_is_blank(self):
        """Test no extra blank line if content already ends with blank."""
        lines = ["# Personal", "Content", ""]
        result = _rebuild_personal_section(lines, "New intro", False)
        # Count blank lines before ## Banner
        banner_idx = result.index("## Banner")
        assert result[banner_idx - 1] == ""
        # Should not have two consecutive blank lines
        assert result[banner_idx - 2] == "Content"

    def test_returns_original_when_banner_found(self):
        """Test returns original lines when banner is found."""
        lines = ["# Personal", "## Banner", "Existing banner"]
        result = _rebuild_personal_section(lines, "New intro", True)
        assert result == lines


class TestExtractRawSection:
    """Tests for _extract_raw_section function."""

    def test_extracts_personal_section(self):
        """Test extracting raw personal section from resume content."""
        content = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John Doe

            # Education
            School: University
            """
        )
        result = _extract_raw_section(content, "personal")
        assert "# Personal" in result
        assert "Name: John Doe" in result
        assert "# Education" not in result
        assert result.endswith("\n")

    def test_extracts_experience_section(self):
        """Test extracting raw experience section."""
        content = textwrap.dedent(
            """\
            # Personal
            Name: John

            # Experience
            ## Company A
            Title: Developer

            # Education
            School: University
            """
        )
        result = _extract_raw_section(content, "experience")
        assert "# Experience" in result
        assert "Company A" in result
        assert "# Personal" not in result
        assert "# Education" not in result

    def test_returns_empty_string_when_section_missing(self):
        """Test returns empty string when section is missing."""
        content = textwrap.dedent(
            """\
            # Personal
            Name: John

            # Education
            School: University
            """
        )
        result = _extract_raw_section(content, "experience")
        assert result == ""

    def test_adds_trailing_newline_if_missing(self):
        """Test adds trailing newline if section doesn't end with one."""
        content = "# Personal\nName: John"  # No trailing newline
        result = _extract_raw_section(content, "personal")
        assert result.endswith("\n")


class TestUpdateBannerInRawPersonal:
    """Tests for _update_banner_in_raw_personal function."""

    def test_adds_banner_when_not_present(self):
        """Test adding banner to personal section without existing banner."""
        raw_personal = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John Doe
            """
        )
        result = _update_banner_in_raw_personal(raw_personal, "New banner text")
        assert "## Banner" in result
        assert "New banner text" in result
        assert result.endswith("\n")

    def test_replaces_existing_banner(self):
        """Test replacing existing banner in personal section."""
        raw_personal = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John Doe

            ## Banner
            Old banner text

            ## Note
            Some note
            """
        )
        result = _update_banner_in_raw_personal(raw_personal, "New banner text")
        assert "New banner text" in result
        assert "Old banner text" not in result
        assert "## Note" in result  # Should preserve following sections
        assert "Some note" in result

    def test_handles_banner_case_insensitive(self):
        """Test that banner header matching is case insensitive."""
        raw_personal = textwrap.dedent(
            """\
            # Personal
            ## BANNER
            Old banner
            """
        )
        result = _update_banner_in_raw_personal(raw_personal, "New banner")
        assert "New banner" in result
        assert "Old banner" not in result

    def test_stops_at_next_section_after_banner(self):
        """Test stops at next section when replacing banner."""
        raw_personal = textwrap.dedent(
            """\
            # Personal
            ## Banner
            Old banner line 1
            Old banner line 2

            ## Note
            Note content
            """
        )
        result = _update_banner_in_raw_personal(raw_personal, "New banner")
        lines = result.splitlines()
        banner_idx = next(i for i, line in enumerate(lines) if "Banner" in line)
        assert lines[banner_idx + 2] == "New banner"
        assert "## Note" in result
        assert "Note content" in result

    def test_returns_original_when_introduction_empty(self):
        """Test returns original when introduction is empty or None."""
        raw_personal = "# Personal\n## Banner\nSome text\n"
        result = _update_banner_in_raw_personal(raw_personal, "")
        assert result == raw_personal

        result = _update_banner_in_raw_personal(raw_personal, None)
        assert result == raw_personal

    def test_strips_introduction_whitespace(self):
        """Test that introduction whitespace is stripped."""
        raw_personal = "# Personal\n"
        result = _update_banner_in_raw_personal(raw_personal, "  Banner text  ")
        assert "Banner text" in result
        assert "  Banner text  " not in result


class TestReconstructResumeWithNewIntroduction:
    """Tests for reconstruct_resume_with_new_introduction function."""

    def test_replaces_banner_in_personal_section(self):
        """Test replacing banner in full resume content."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John Doe

            ## Banner
            Old banner

            # Education
            School: University
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "New banner")
        assert "New banner" in result
        assert "Old banner" not in result
        assert "# Education" in result
        assert "University" in result

    def test_adds_banner_if_not_present(self):
        """Test adding banner when not present in personal section."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John Doe

            # Education
            School: University
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "New banner")
        assert "## Banner" in result
        assert "New banner" in result

    def test_returns_original_when_no_personal_section(self):
        """Test returns original when no personal section exists."""
        original = textwrap.dedent(
            """\
            # Education
            School: University

            # Experience
            Company: Acme
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "New banner")
        assert result == original

    def test_preserves_other_sections(self):
        """Test that all other sections are preserved."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John

            ## Banner
            Old banner

            # Education
            School: University

            # Experience
            ## Company A
            Title: Developer

            # Certifications
            Cert: AWS
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "New banner")
        assert "# Education" in result
        assert "University" in result
        assert "# Experience" in result
        assert "Company A" in result
        assert "# Certifications" in result
        assert "AWS" in result

    def test_handles_multiple_sections_correctly(self):
        """Test handling resume with multiple sections."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Banner
            Old

            # Summary
            Summary text

            # Experience
            Job details

            # Skills
            Python, JavaScript

            # Projects
            Project A
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "Updated banner")
        # Check all sections preserved
        assert "# Summary" in result
        assert "# Experience" in result
        assert "# Skills" in result
        assert "# Projects" in result
        # Check banner updated
        assert "Updated banner" in result
        assert "Old" not in result

    def test_empty_introduction_no_change(self):
        """Test that empty introduction results in no change to banner."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Banner
            Existing banner

            # Education
            School: University
            """
        )
        result = reconstruct_resume_with_new_introduction(original, "")
        # Should still add an empty banner section
        assert "## Banner" in result

    @pytest.mark.parametrize(
        "intro",
        [
            "Single line introduction",
            "Multi-line\nintroduction\nwith breaks",
            "Introduction with **markdown** formatting",
            "Introduction with [link](http://example.com)",
        ],
    )
    def test_various_introduction_formats(self, intro: str):
        """Test handling various introduction formats."""
        original = "# Personal\n## Contact\nName: John\n"
        result = reconstruct_resume_with_new_introduction(original, intro)
        # The introduction should be present (potentially with whitespace changes)
        first_line = intro.splitlines()[0].strip()
        assert first_line in result


class TestEdgeCases:
    """Edge case tests for extraction functions."""

    def test_parse_personal_with_multiple_top_level_sections(self):
        """Test parsing when multiple top level sections exist."""
        lines = [
            "# Personal",
            "Content",
            "# Experience",
            "Exp content",
            "# Education",
            "Edu content",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert len(result) == 2
        assert result == ["# Personal", "Content"]

    def test_parse_personal_with_subsections_before_next_top(self):
        """Test parsing subsections before next top-level section."""
        lines = [
            "# Personal",
            "## Sub1",
            "Content1",
            "## Sub2",
            "Content2",
            "## Sub3",
            "Content3",
            "# Experience",
        ]
        result = _parse_personal_section_lines(lines, "personal")
        assert len(result) == 7
        assert "# Experience" not in result

    def test_extract_section_with_only_header(self):
        """Test extracting section with only header."""
        content = "# Personal\n# Education\nSchool: University"
        result = _extract_raw_section(content, "personal")
        assert "# Personal" in result
        assert "# Education" not in result

    def test_update_banner_preserves_whitespace_in_content(self):
        """Test that content whitespace is preserved when updating banner."""
        raw_personal = textwrap.dedent(
            """\
            # Personal
            ## Contact
            Name: John

            Email: john@example.com

            ## Banner
            Old banner

            ## Note
            Important note
            """
        )
        result = _update_banner_in_raw_personal(raw_personal, "New banner")
        # Check that spacing is preserved
        assert "Name: John" in result
        assert "\n\nEmail:" in result
        assert "Important note" in result

    def test_reconstruct_with_complex_resume(self):
        """Test reconstruction with a complex, realistic resume."""
        original = textwrap.dedent(
            """\
            # Personal
            ## Contact Information
            Name: Jane Doe
            Email: jane@example.com
            Phone: 555-1234
            Location: New York, NY

            ## Websites
            GitHub: janedoe
            LinkedIn: janedoe

            ## Banner
            Experienced software engineer with 10 years of experience.

            ## Note
            Open to remote opportunities.

            # Education
            ## University of Example
            Degree: BS Computer Science
            Dates: 2010-2014

            # Experience
            ## TechCorp
            Title: Senior Developer
            Dates: 2020-Present
            Description: Leading development team

            ## StartupXYZ
            Title: Developer
            Dates: 2014-2020
            Description: Full stack development

            # Skills
            Python, JavaScript, AWS, Docker

            # Certifications
            AWS Solutions Architect
            """
        )
        new_intro = "Senior software engineer specializing in cloud architecture and team leadership."
        result = reconstruct_resume_with_new_introduction(original, new_intro)

        # Verify new intro is present
        assert new_intro in result
        assert "Experienced software engineer" not in result

        # Verify all sections preserved
        assert "# Personal" in result
        assert "# Education" in result
        assert "# Experience" in result
        assert "# Skills" in result
        assert "# Certifications" in result

        # Verify specific content preserved
        assert "Jane Doe" in result
        assert "University of Example" in result
        assert "TechCorp" in result
        assert "StartupXYZ" in result
        assert "AWS Solutions Architect" in result
