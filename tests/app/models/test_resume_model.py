from resume_editor.app.models.resume_model import Resume


def test_resume_initialization_with_new_fields():
    """Test that a Resume object can be initialized with the new fields."""
    resume = Resume(
        user_id=1,
        name="Test Resume",
        content="Some content",
        is_base=False,
        job_description="A job description",
        parent_id=1,
        notes="These are some notes.",
        introduction="This is an introduction.",
    )
    assert resume.user_id == 1
    assert resume.name == "Test Resume"
    assert resume.content == "Some content"
    assert resume.is_active is True  # default
    assert resume.is_base is False
    assert resume.job_description == "A job description"
    assert resume.parent_id == 1
    assert resume.notes == "These are some notes."
    assert resume.introduction == "This is an introduction."


def test_resume_initialization_defaults_for_new_fields():
    """Test that a Resume object can be initialized with default None for new fields."""
    resume = Resume(
        user_id=1,
        name="Test Resume",
        content="Some content",
        is_base=False,
        job_description="A job description",
        parent_id=1,
    )
    assert resume.notes is None
    assert resume.introduction is None


def test_resume_is_base_defaults_to_true():
    """Test that is_base defaults to True if not provided."""
    resume = Resume(user_id=1, name="Test Resume", content="Some content")
    assert resume.is_base is True
