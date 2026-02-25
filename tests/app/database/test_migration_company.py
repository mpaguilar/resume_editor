"""Tests for the company column database migration."""

import pytest
import sqlalchemy as sa
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

from resume_editor.app.models.resume_model import Resume as DatabaseResume
from resume_editor.app.models.resume_model import ResumeData


class TestCompanyMigration:
    """Tests for the company column migration."""

    @pytest.fixture
    def engine(self):
        """Create an in-memory database engine."""
        return create_engine("sqlite:///:memory:")

    @pytest.fixture
    def connection(self, engine):
        """Create a database connection."""
        with engine.connect() as conn:
            yield conn

    def test_company_column_exists_after_migration(self, engine, connection):
        """Test that the company column exists after migration."""
        DatabaseResume.metadata.create_all(engine)
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("resumes")]
        assert "company" in columns

    def test_company_column_is_nullable(self, engine, connection):
        """Test that the company column is nullable."""
        DatabaseResume.metadata.create_all(engine)
        inspector = inspect(engine)
        columns = inspector.get_columns("resumes")
        company_col = next(col for col in columns if col["name"] == "company")
        assert company_col["nullable"] is True

    def test_company_column_type_is_string(self, engine, connection):
        """Test that the company column is a String type."""
        DatabaseResume.metadata.create_all(engine)
        inspector = inspect(engine)
        columns = inspector.get_columns("resumes")
        company_col = next(col for col in columns if col["name"] == "company")
        assert isinstance(company_col["type"], sa.String)

    def test_company_column_max_length(self, engine, connection):
        """Test that the company column has a max length of 255."""
        DatabaseResume.metadata.create_all(engine)
        inspector = inspect(engine)
        columns = inspector.get_columns("resumes")
        company_col = next(col for col in columns if col["name"] == "company")
        assert company_col["type"].length == 255

    def test_can_insert_resume_with_company(self, engine):
        """Test that a resume can be inserted with a company value."""
        DatabaseResume.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
            company="Acme Corp",
        )
        resume = DatabaseResume(data=data)
        session.add(resume)
        session.commit()
        result = session.query(DatabaseResume).first()
        assert result.company == "Acme Corp"
        session.close()

    def test_can_insert_resume_without_company(self, engine):
        """Test that a resume can be inserted without a company value (NULL)."""
        DatabaseResume.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        data = ResumeData(
            user_id=1,
            name="Test Resume",
            content="Test content",
        )
        resume = DatabaseResume(data=data)
        session.add(resume)
        session.commit()
        result = session.query(DatabaseResume).first()
        assert result.company is None
        session.close()
