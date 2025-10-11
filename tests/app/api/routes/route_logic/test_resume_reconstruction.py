from resume_editor.app.api.routes.route_logic.resume_reconstruction import (
    reconstruct_resume_markdown,
)
from resume_editor.app.api.routes.route_models import (
    EducationResponse,
    PersonalInfoResponse,
)


def test_reconstruct_resume_markdown_with_empty_personal_info():
    """Test that an empty but non-None personal info section is not rendered."""
    personal_info = PersonalInfoResponse()  # This will serialize to an empty string
    education_info = EducationResponse(
        degrees=[
            {
                "school": "University of Testing",
                "degree": "B.Sc. in Testing",
            },
        ],
    )

    result = reconstruct_resume_markdown(
        personal_info=personal_info,
        education=education_info,
    )

    assert "# Personal" not in result
    assert "# Education" in result
    assert "University of Testing" in result
