"""Integration tests for company field functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from resume_editor.app.api.routes.route_logic.resume_crud import (
    ResumeCreateParams,
    ResumeUpdateParams,
    create_resume,
    update_resume,
)
from resume_editor.app.api.routes.route_logic.resume_validation import (
    validate_company_and_notes,
    validate_refinement_form,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.resume_model import ResumeData


class TestCompanyFieldIntegration:
    """Integration tests for company field across the stack."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        DatabaseResume.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        yield db
        db.close()
        DatabaseResume.metadata.drop_all(bind=engine)

    def test_full_create_resume_with_company_flow(self, db_session):
        """Test creating a resume with company through all layers."""
        params = ResumeCreateParams(
            user_id=1,
            name="Test Resume",
            content="Content",
            company="Acme Corp",
            notes="Some notes",
        )
        resume = create_resume(db_session, params)

        assert resume.company == "Acme Corp"
        assert resume.notes == "Some notes"

        # Verify it can be retrieved
        retrieved = db_session.query(DatabaseResume).filter_by(id=resume.id).first()
        assert retrieved.company == "Acme Corp"
        assert retrieved.notes == "Some notes"

    def test_full_update_resume_company_flow(self, db_session):
        """Test updating a resume's company through all layers."""
        # Create initial resume
        create_params = ResumeCreateParams(
            user_id=1, name="Test Resume", content="Content"
        )
        resume = create_resume(db_session, create_params)
        assert resume.company is None

        # Update with company
        update_params = ResumeUpdateParams(company="New Corp", notes="New notes")
        updated = update_resume(db_session, resume, update_params)

        assert updated.company == "New Corp"
        assert updated.notes == "New notes"

        # Verify in database
        db_session.refresh(resume)
        assert resume.company == "New Corp"

    def test_validation_blocks_invalid_company(self, db_session):
        """Test that validation blocks resumes with invalid company."""
        invalid_company = "A" * 256  # Exceeds max length

        result = validate_company_and_notes(invalid_company, None)
        assert result.is_valid is False
        assert "company" in result.errors

    def test_refinement_form_validation(self, db_session):
        """Test refinement form validation with company."""
        # Valid form
        result = validate_refinement_form(
            job_description="Software Engineer", company="Acme Corp", notes="Some notes"
        )
        assert result.is_valid is True

        # Invalid - missing job description
        result = validate_refinement_form(
            job_description=None, company="Acme Corp", notes=None
        )
        assert result.is_valid is False
        assert "job_description" in result.errors

        # Invalid - company too long
        result = validate_refinement_form(
            job_description="Software Engineer", company="A" * 256, notes=None
        )
        assert result.is_valid is False
        assert "company" in result.errors

    def test_company_sorting_integration(self, db_session):
        """Test company sorting in database queries."""
        # Create resumes with different companies
        companies = ["Zebra Corp", "Alpha Corp", None, "Beta Corp"]
        for i, company in enumerate(companies):
            params = ResumeCreateParams(
                user_id=1,
                name=f"Resume {i}",
                content="Content",
                is_base=False,
                company=company,
            )
            create_resume(db_session, params)

        # Test ascending sort
        from resume_editor.app.api.routes.route_logic.resume_crud import (
            get_user_resumes,
        )

        resumes_asc = get_user_resumes(db_session, user_id=1, sort_by="company_asc")
        companies_asc = [r.company for r in resumes_asc]
        assert companies_asc == [None, "Alpha Corp", "Beta Corp", "Zebra Corp"]

        # Test descending sort
        resumes_desc = get_user_resumes(db_session, user_id=1, sort_by="company_desc")
        companies_desc = [r.company for r in resumes_desc]
        assert companies_desc == ["Zebra Corp", "Beta Corp", "Alpha Corp", None]

    def test_filter_by_company_integration(self, db_session):
        """Test filtering resumes by company field."""
        # Create resumes
        for company in ["Acme Corp", "Beta Inc", None]:
            params = ResumeCreateParams(
                user_id=1,
                name="Test",
                content="Content",
                is_base=False,
                company=company,
            )
            create_resume(db_session, params)

        # Search for "Acme"
        from resume_editor.app.api.routes.route_logic.resume_crud import (
            apply_resume_filter,
        )

        query = db_session.query(DatabaseResume)
        filtered = apply_resume_filter(query, "Acme")
        results = filtered.all()

        assert len(results) == 1
        assert results[0].company == "Acme Corp"
