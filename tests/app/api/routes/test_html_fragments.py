from datetime import datetime
from unittest.mock import MagicMock, patch
import textwrap

import pytest
from bs4 import BeautifulSoup

from resume_editor.app.api.routes.html_fragments import (
    _create_refine_result_html,
    _date_format_filter,
    _generate_resume_detail_html,
    _generate_resume_list_html,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.user import User as DBUser


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
    )
    user.id = 1
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Test Resume",
        content="some content",
    )
    resume.id = 1
    resume.created_at = datetime(2023, 1, 15)
    resume.updated_at = datetime(2023, 1, 16)
    return resume


@pytest.fixture
def test_refined_resume(test_user):
    """Fixture for a test refined resume."""
    resume = DatabaseResume(
        user_id=test_user.id,
        name="Refined Resume",
        content="some refined content",
        is_base=False,
        parent_id=1,
    )
    resume.id = 2
    resume.created_at = datetime(2023, 2, 20)
    resume.updated_at = datetime(2023, 2, 21)
    return resume


def test_date_format_filter():
    """Test the _date_format_filter for correct date formatting."""
    dt = datetime(2025, 10, 3)
    assert _date_format_filter(value=dt) == "2025-10-03"
    assert _date_format_filter(value=dt, format_string="%d-%m-%Y") == "03-10-2025"
    assert _date_format_filter(value=None) == ""


def test_date_format_filter_registration():
    """Test that the date format filters are registered in the Jinja env."""
    from resume_editor.app.api.routes.html_fragments import env

    assert "date_format" in env.filters
    assert "strftime" in env.filters
    assert env.filters["date_format"] is _date_format_filter
    assert env.filters["strftime"] is _date_format_filter


def test_generate_resume_list_html_empty():
    """Test that _generate_resume_list_html returns the correct message for an empty list."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _generate_resume_list_html(
            base_resumes=[],
            refined_resumes=[],
            selected_resume_id=None,
            sort_by="name_asc",
            wrap_in_div=False,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            base_resumes=[],
            refined_resumes=[],
            selected_resume_id=None,
            sort_by="name_asc",
        )


def test_generate_resume_list_html(test_resume):
    """Test that _generate_resume_list_html correctly handles no selection."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        resumes = [test_resume]
        _generate_resume_list_html(
            base_resumes=resumes,
            refined_resumes=[],
            selected_resume_id=None,
            sort_by="name_asc",
            wrap_in_div=False,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            base_resumes=resumes,
            refined_resumes=[],
            selected_resume_id=None,
            sort_by="name_asc",
        )


def test_generate_resume_list_html_template(test_resume):
    """Test that _generate_resume_list_html renders the correct template."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        resumes = [test_resume]
        selected_id = 1
        _generate_resume_list_html(
            base_resumes=resumes,
            refined_resumes=[],
            selected_resume_id=selected_id,
            sort_by="name_asc",
            wrap_in_div=False,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            base_resumes=resumes,
            refined_resumes=[],
            selected_resume_id=selected_id,
            sort_by="name_asc",
        )


def test_generate_resume_list_html_output(test_resume, test_refined_resume):
    """Test that _generate_resume_list_html renders with date stamps and correct wrapping."""
    # This test uses the actual template, no mocking of jinja env.
    base_resumes = [test_resume]
    refined_resumes = [test_refined_resume]

    # Test without the wrapper div
    html_output_no_wrap = _generate_resume_list_html(
        base_resumes=base_resumes,
        refined_resumes=refined_resumes,
        selected_resume_id=None,
        sort_by="name_asc",
        wrap_in_div=False,
    )
    assert not html_output_no_wrap.startswith('<div id="resume-list">')

    # Test with the wrapper div
    html_output_with_wrap = _generate_resume_list_html(
        base_resumes=base_resumes,
        refined_resumes=refined_resumes,
        selected_resume_id=None,
        sort_by="name_asc",
        wrap_in_div=True,
    )
    assert html_output_with_wrap.startswith('<div id="resume-list">')
    assert html_output_with_wrap.endswith("</div>")

    # Use the wrapped output for content assertions
    html_output = html_output_with_wrap

    # Base resume assertions
    assert "Test Resume" in html_output
    assert "Created: 2023-01-15" in html_output
    assert "Updated: 2023-01-16" in html_output
    assert "&bull;" in html_output

    # Refined resume assertions
    assert "Refined Resume" in html_output
    assert "Created: 2023-02-20" in html_output
    assert "Updated: 2023-02-21" in html_output
    assert '<input type="text"' in html_output
    assert 'id="refined-resume-search"' in html_output
    assert 'placeholder="Filter applied resumes..."' in html_output

    # Sorting controls assertions
    assert "Sort by:" in html_output
    assert 'hx-get="/api/resumes?sort_by=name_desc"' in html_output
    assert "Name &uarr;" in html_output
    assert 'hx-get="/api/resumes?sort_by=created_at_desc"' in html_output
    assert "Created" in html_output
    assert 'hx-get="/api/resumes?sort_by=updated_at_desc"' in html_output
    assert "Modified" in html_output

    # Link assertions
    soup = BeautifulSoup(html_output, "html.parser")
    resume_items = soup.find_all("div", class_="resume-item")
    assert len(resume_items) == 2

    # First item is base resume
    base_resume_item = resume_items[0]
    assert "Test Resume" in base_resume_item.text
    edit_link = base_resume_item.find(
        "a", string=lambda s: s and s.strip() == "Edit"
    )
    assert edit_link is not None
    assert edit_link["href"] == f"/resumes/{test_resume.id}/edit"

    # Second item is refined resume
    refined_resume_item = resume_items[1]
    assert "Refined Resume" in refined_resume_item.text
    view_link = refined_resume_item.find(
        "a", string=lambda s: s and s.strip() == "View"
    )
    assert view_link is not None
    assert view_link["href"] == f"/resumes/{test_refined_resume.id}/view"


def test_generate_resume_list_html_output_no_dates(test_user):
    """Test that _generate_resume_list_html renders correctly with no date stamps."""
    base_resume_no_dates = DatabaseResume(
        user_id=test_user.id,
        name="Test Resume No Dates",
        content="some content",
    )
    base_resume_no_dates.id = 3
    base_resume_no_dates.created_at = None
    base_resume_no_dates.updated_at = None

    html_output = _generate_resume_list_html(
        base_resumes=[base_resume_no_dates],
        refined_resumes=[],
        selected_resume_id=None,
        sort_by="updated_at_desc",
        wrap_in_div=False,
    )

    assert "Test Resume No Dates" in html_output
    assert "Created:" not in html_output
    assert "Updated:" not in html_output
    assert "&bull;" not in html_output


def test_generate_resume_detail_html_template_usage(test_resume):
    """Test that _generate_resume_detail_html renders via template."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _generate_resume_detail_html(test_resume)
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_detail.html"
        )
        mock_template.render.assert_called_once_with(resume=test_resume)


def test_create_refine_result_html_template():
    """Test that _create_refine_result_html renders the correct template."""
    resume_id = 123
    target_section_val = "experience"
    refined_content = "some <refined> content"
    job_description = "A great job"

    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        _create_refine_result_html(
            resume_id,
            target_section_val,
            refined_content,
            job_description,
            introduction=None,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_refine_result.html"
        )
        mock_template.render.assert_called_once_with(
            resume_id=resume_id,
            target_section_val=target_section_val,
            refined_content=refined_content,
            job_description=job_description,
            introduction=None,
        )


def test_create_refine_result_html_output():
    """Test that the rendered HTML from _create_refine_result_html is correct."""
    resume_id = 42
    target_section_val = "experience"
    refined_content = "This is *refined* markdown."
    job_description = "A job description"
    introduction = "This is an intro."

    html_output = _create_refine_result_html(
        resume_id,
        target_section_val,
        refined_content,
        job_description=job_description,
        introduction=introduction,
    )

    assert 'id="refine-result"' in html_output
    assert (
        '<label for="introduction" class="block font-semibold text-md mb-1">Introduction</label>'
        in html_output
    )
    assert '<textarea id="introduction" name="introduction"' in html_output
    assert 'class="prose prose-sm' not in html_output
    assert ">This is an intro.</textarea>" in html_output
    assert '<input type="hidden" name="introduction"' not in html_output
    assert 'hx-post="/api/resumes/42/refine/accept"' in html_output
    assert 'name="target_section" value="experience"' in html_output
    assert '<textarea name="refined_content"' in html_output
    assert ">This is *refined* markdown.</textarea>" in html_output
    assert 'hx-post="/api/resumes/42/refine/save_as_new"' in html_output
    assert "Accept & Overwrite" in html_output
    assert 'hx-post="/api/resumes/42/refine/discard"' in html_output
    assert "Discard" in html_output
    assert "Save as New" in html_output
    assert "Reject" not in html_output
    assert 'name="job_description" value="A job description"' in html_output


def test_generate_resume_list_html_with_refined(test_refined_resume):
    """Test that _generate_resume_list_html correctly handles refined resumes."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        resumes = [test_refined_resume]
        _generate_resume_list_html(
            base_resumes=[],
            refined_resumes=resumes,
            selected_resume_id=None,
            sort_by="name_asc",
            wrap_in_div=False,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            base_resumes=[],
            refined_resumes=resumes,
            selected_resume_id=None,
            sort_by="name_asc",
        )


def test_generate_resume_list_html_with_both(test_resume, test_refined_resume):
    """Test that _generate_resume_list_html correctly handles both resume types."""
    with patch("resume_editor.app.api.routes.html_fragments.env") as mock_env:
        mock_template = MagicMock()
        mock_env.get_template.return_value = mock_template
        base_resumes = [test_resume]
        refined_resumes = [test_refined_resume]
        _generate_resume_list_html(
            base_resumes=base_resumes,
            refined_resumes=refined_resumes,
            selected_resume_id=None,
            sort_by="name_asc",
            wrap_in_div=False,
        )
        mock_env.get_template.assert_called_once_with(
            "partials/resume/_resume_list.html"
        )
        mock_template.render.assert_called_once_with(
            base_resumes=base_resumes,
            refined_resumes=refined_resumes,
            selected_resume_id=None,
            sort_by="name_asc",
        )


def test_generate_resume_detail_html_for_base_resume(test_resume):
    """Test detail view for a base resume."""
    # is_base is True by default in the fixture
    html_output = _generate_resume_detail_html(test_resume)
    soup = BeautifulSoup(html_output, "html.parser")

    # Check that refine button and form are present
    assert soup.find("button", string=lambda s: s and s.strip() == "AI Refine")
    assert soup.find("div", id="refine-form-container-1")

    # Check refine form for "Generate Introduction" checkbox
    assert soup.find("label", attrs={"for": "generate_introduction"})
    assert soup.find("input", attrs={"name": "generate_introduction", "type": "checkbox"})

    # Check for export button and modal
    export_button = soup.find(
        "button", string=lambda s: s and s.strip() == "Export"
    )
    assert export_button is not None
    assert (
        export_button["onclick"]
        == "document.getElementById('export-modal-1').classList.remove('hidden')"
    )
    export_modal = soup.find("div", id="export-modal-1")
    assert export_modal is not None

    # Check that job description details are not present
    assert "Job Description Used for Refinement" not in html_output

    # Check that notes form is NOT present
    assert not soup.find("textarea", attrs={"name": "notes"})


def test_generate_resume_detail_html_base_with_children(
    test_resume, test_refined_resume
):
    """Test detail view for a base resume with children includes refined search."""
    # Add child to the base resume
    test_resume.children = [test_refined_resume]

    html_output = _generate_resume_detail_html(test_resume)

    # Check for Refined Versions section
    assert "Refined Versions" in html_output

    # Check for search input
    assert 'id="refined-search-1"' in html_output
    assert 'onkeyup="filterRefinedResumes(1)"' in html_output
    assert 'placeholder="Search refined versions by name..."' in html_output

    # Check for list of refined resumes
    assert 'id="refined-list-1"' in html_output
    assert "Refined Resume" in html_output
    assert 'hx-get="/api/resumes/2/html"' in html_output
    assert 'class="text-blue-600 hover:underline resume-name"' in html_output

    # Check for javascript function
    assert "function filterRefinedResumes(resumeId)" in html_output


def test_generate_resume_detail_html_for_refined_resume(test_refined_resume):
    """Test detail view for a refined resume shows correct UI elements."""
    test_refined_resume.job_description = "A great job description."
    html_output = _generate_resume_detail_html(test_refined_resume)
    soup = BeautifulSoup(html_output, "html.parser")

    # Check that refine button and form are NOT present
    assert not soup.find("button", string=lambda s: s and s.strip() == "AI Refine")
    assert not soup.find("div", id=f"refine-form-container-{test_refined_resume.id}")

    # Check for export button and modal
    export_button = soup.find(
        "button", string=lambda s: s and s.strip() == "Export"
    )
    assert export_button is not None
    assert (
        export_button["onclick"]
        == f"document.getElementById('export-modal-{test_refined_resume.id}').classList.remove('hidden')"
    )
    export_modal = soup.find("div", id=f"export-modal-{test_refined_resume.id}")
    assert export_modal is not None

    # Check that job description details are present
    assert "Job Description Used for Refinement" in html_output
    assert soup.find("details")
    assert "A great job description." in html_output

    # Check notes form is present
    notes_textarea = soup.find("textarea", attrs={"name": "notes"})
    assert notes_textarea is not None
    assert notes_textarea["hx-post"] == f"/api/resumes/{test_refined_resume.id}/notes"


@pytest.mark.parametrize("intro", [None, ""])
def test_create_refine_result_html_output_no_introduction(intro):
    """Test that the rendered HTML from _create_refine_result_html is correct when no introduction is provided."""
    resume_id = 42
    target_section_val = "experience"
    refined_content = "This is *refined* markdown."
    job_description = "A job description"

    html_output = _create_refine_result_html(
        resume_id,
        target_section_val,
        refined_content,
        job_description=job_description,
        introduction=intro,
    )

    assert 'id="refine-result"' in html_output

    # Check that introduction elements are not present
    assert '<label for="introduction"' not in html_output
    assert '<textarea id="introduction" name="introduction"' not in html_output
    assert "Introduction</h4>" not in html_output

    # Check that other elements are present
    assert 'hx-post="/api/resumes/42/refine/accept"' in html_output
    assert 'name="target_section" value="experience"' in html_output
    assert '<textarea name="refined_content"' in html_output
    assert ">This is *refined* markdown.</textarea>" in html_output


def test_generate_resume_detail_html_refined_resume_no_jd(test_refined_resume):
    """Test detail view for a refined resume with no JD shows neither UI."""
    test_refined_resume.job_description = None  # Explicitly set to None
    html_output = _generate_resume_detail_html(test_refined_resume)

    # Check that refine button and form are NOT present
    assert "AI Refine" not in html_output
    assert 'id="refine-form-container-2"' not in html_output

    # Check that job description details are NOT present
    assert "Job Description Used for Refinement" not in html_output

    # Check notes form for auto-save functionality
    assert '<form hx-post="/api/resumes/2/notes"' not in html_output
    assert '<textarea name="notes"' in html_output
    assert 'hx-post="/api/resumes/2/notes"' in html_output
    assert 'hx-trigger="keyup changed delay:500ms"' in html_output
    assert 'hx-target="#notes-save-status-2"' in html_output
    assert 'hx-swap="innerHTML"' in html_output
    assert "Save Notes" not in html_output
    assert 'id="notes-save-status-2"' in html_output


def test_generate_resume_detail_html_refined_resume_with_notes(test_refined_resume):
    """Test detail view for a refined resume displays notes in the form."""
    test_refined_resume.notes = "These are some important notes."
    html_output = _generate_resume_detail_html(test_refined_resume)

    # Check that notes form is present and contains the notes
    assert '<form hx-post="/api/resumes/2/notes"' not in html_output
    assert ">These are some important notes.</textarea>" in html_output
    assert 'hx-post="/api/resumes/2/notes"' in html_output
    assert 'hx-trigger="keyup changed delay:500ms"' in html_output
    assert 'hx-target="#notes-save-status-2"' in html_output
    assert 'hx-swap="innerHTML"' in html_output
    assert "Save Notes" not in html_output
    assert 'id="notes-save-status-2"' in html_output


@pytest.mark.parametrize(
    "intro_text, should_be_present",
    [
        ("This is a saved introduction.", True),
        (None, False),
        ("", False),
    ],
)
def test_generate_resume_detail_html_with_introduction(
    test_refined_resume, intro_text, should_be_present
):
    """Test detail view for a refined resume displays introduction when present."""
    test_refined_resume.introduction = intro_text
    html_output = _generate_resume_detail_html(test_refined_resume)

    intro_heading = (
        '<h3 class="text-lg font-medium text-gray-900 mb-2">Introduction</h3>'
    )
    if should_be_present:
        # Check for the whole structure to be more robust, as per testing notes.
        expected_structure = textwrap.dedent(
            f"""\
            <div class="my-4 p-4 border rounded-lg bg-gray-50">
                <h3 class="text-lg font-medium text-gray-900 mb-2">Introduction</h3>
                <div class="mt-2 prose max-w-none">
                    <pre class="whitespace-pre-wrap bg-gray-100 p-2 rounded text-sm">{intro_text}</pre>
                </div>
            </div>"""
        )
        # Normalize whitespace in both actual and expected to make comparison robust
        html_output_normalized = " ".join(html_output.split())
        expected_structure_normalized = " ".join(expected_structure.split())

        assert expected_structure_normalized in html_output_normalized
    else:
        assert intro_heading not in html_output
        assert "whitespace-pre-wrap" not in html_output


def test_generate_resume_detail_html_base_resume_does_not_show_introduction(
    test_resume,
):
    """Test detail view for a base resume does not show introduction even if present."""
    test_resume.introduction = "This is an introduction on a base resume."
    html_output = _generate_resume_detail_html(test_resume)

    intro_heading = (
        '<h3 class="text-lg font-medium text-gray-900 mb-2">Introduction</h3>'
    )
    assert intro_heading not in html_output
    assert "whitespace-pre-wrap" not in html_output
    assert "This is an introduction on a base resume." not in html_output
