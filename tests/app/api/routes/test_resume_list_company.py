"""Tests for resume list endpoint with company sorting."""

import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from resume_editor.app.api.routes.route_logic.resume_crud import (
    get_user_resumes,
    get_user_resumes_with_pagination,
)
from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.resume_model import ResumeData


class TestCompanySorting:
    """Tests for sorting by company field."""

    @pytest.fixture
    def db_with_resumes(self):
        """Create test database with resumes having different companies."""
        engine = create_engine("sqlite:///:memory:")
        DatabaseResume.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Create resumes with different companies
        resumes = [
            DatabaseResume(
                data=ResumeData(
                    user_id=1,
                    name="Resume A",
                    content="Content",
                    is_base=False,
                    company="Zebra Corp",
                )
            ),
            DatabaseResume(
                data=ResumeData(
                    user_id=1,
                    name="Resume B",
                    content="Content",
                    is_base=False,
                    company="Alpha Corp",
                )
            ),
            DatabaseResume(
                data=ResumeData(
                    user_id=1,
                    name="Resume C",
                    content="Content",
                    is_base=False,
                    company=None,
                )
            ),
            DatabaseResume(
                data=ResumeData(
                    user_id=1,
                    name="Resume D",
                    content="Content",
                    is_base=False,
                    company="Beta Corp",
                )
            ),
        ]

        db.add_all(resumes)
        db.commit()
        yield db
        db.close()
        DatabaseResume.metadata.drop_all(bind=engine)

    def test_sort_by_company_asc(self, db_with_resumes):
        """Test sorting resumes by company ascending."""
        resumes = get_user_resumes(db_with_resumes, user_id=1, sort_by="company_asc")
        companies = [r.company for r in resumes if not r.is_base]
        # NULLs typically come first in SQLite
        assert companies == [None, "Alpha Corp", "Beta Corp", "Zebra Corp"]

    def test_sort_by_company_desc(self, db_with_resumes):
        """Test sorting resumes by company descending."""
        resumes = get_user_resumes(db_with_resumes, user_id=1, sort_by="company_desc")
        companies = [r.company for r in resumes if not r.is_base]
        assert companies == ["Zebra Corp", "Beta Corp", "Alpha Corp", None]
