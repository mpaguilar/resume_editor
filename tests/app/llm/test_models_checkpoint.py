"""Tests for checkpoint system models in resume_editor/app/llm/models.py.

These tests verify the RefinedRoleRecord and RunningLog models.
"""

import logging
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from resume_editor.app.llm.models import (
    JobAnalysis,
    RefinedRoleRecord,
    RunningLog,
)

log = logging.getLogger(__name__)


class TestRefinedRoleRecord:
    """Tests for RefinedRoleRecord model."""

    def test_valid_creation(self) -> None:
        """Test creating a valid RefinedRoleRecord."""
        now = datetime.now()
        record = RefinedRoleRecord(
            original_index=0,
            company="Example Corp",
            title="Senior Developer",
            refined_description="Led development of key features...",
            relevant_skills=["Python", "FastAPI", "PostgreSQL"],
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31),
            timestamp=now,
        )

        assert record.original_index == 0
        assert record.company == "Example Corp"
        assert record.title == "Senior Developer"
        assert record.refined_description == "Led development of key features..."
        assert record.relevant_skills == ["Python", "FastAPI", "PostgreSQL"]
        assert record.start_date == datetime(2020, 1, 1)
        assert record.end_date == datetime(2023, 12, 31)
        assert record.timestamp == now

    def test_optional_end_date(self) -> None:
        """Test that end_date can be None (for current positions)."""
        now = datetime.now()
        record = RefinedRoleRecord(
            original_index=1,
            company="Current Corp",
            title="Lead Developer",
            refined_description="Currently leading the team...",
            relevant_skills=["Python", "AWS"],
            start_date=datetime(2024, 1, 1),
            end_date=None,
            timestamp=now,
        )

        assert record.end_date is None

    def test_empty_skills_list(self) -> None:
        """Test that relevant_skills can be empty."""
        now = datetime.now()
        record = RefinedRoleRecord(
            original_index=0,
            company="Test Corp",
            title="Developer",
            refined_description="Description here...",
            relevant_skills=[],
            start_date=datetime(2020, 1, 1),
            end_date=None,
            timestamp=now,
        )

        assert record.relevant_skills == []

    def test_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            RefinedRoleRecord(
                original_index=0,
                company="Test Corp",
                # Missing title
                refined_description="Description...",
                relevant_skills=["Python"],
                start_date=datetime(2020, 1, 1),
                timestamp=datetime.now(),
            )


class TestRunningLog:
    """Tests for RunningLog model."""

    def test_valid_creation_empty_roles(self) -> None:
        """Test creating a RunningLog with empty refined_roles."""
        now = datetime.now()
        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Looking for a Python developer...",
            job_analysis=None,
            refined_roles=[],
            created_at=now,
            updated_at=now,
        )

        assert log_entry.resume_id == 1
        assert log_entry.user_id == 2
        assert log_entry.job_description == "Looking for a Python developer..."
        assert log_entry.job_analysis is None
        assert log_entry.refined_roles == []
        assert log_entry.created_at == now
        assert log_entry.updated_at == now

    def test_with_job_analysis(self) -> None:
        """Test RunningLog with job_analysis populated."""
        now = datetime.now()
        job_analysis = JobAnalysis(
            key_skills=["Python", "FastAPI"],
            primary_duties=["Build APIs", "Write tests"],
            themes=["remote work", "agile"],
        )

        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Looking for a Python developer...",
            job_analysis=job_analysis,
            refined_roles=[],
            created_at=now,
            updated_at=now,
        )

        assert log_entry.job_analysis is not None
        assert log_entry.job_analysis.key_skills == ["Python", "FastAPI"]

    def test_with_refined_roles(self) -> None:
        """Test RunningLog with refined_roles populated."""
        now = datetime.now()
        role_record = RefinedRoleRecord(
            original_index=0,
            company="Example Corp",
            title="Developer",
            refined_description="Did cool things...",
            relevant_skills=["Python"],
            start_date=datetime(2020, 1, 1),
            end_date=None,
            timestamp=now,
        )

        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Looking for a Python developer...",
            job_analysis=None,
            refined_roles=[role_record],
            created_at=now,
            updated_at=now,
        )

        assert len(log_entry.refined_roles) == 1
        assert log_entry.refined_roles[0].company == "Example Corp"

    def test_multiple_roles(self) -> None:
        """Test RunningLog with multiple refined roles."""
        now = datetime.now()
        roles = [
            RefinedRoleRecord(
                original_index=0,
                company="First Corp",
                title="Junior Dev",
                refined_description="First job...",
                relevant_skills=["Python"],
                start_date=datetime(2018, 1, 1),
                end_date=datetime(2020, 1, 1),
                timestamp=now,
            ),
            RefinedRoleRecord(
                original_index=1,
                company="Second Corp",
                title="Senior Dev",
                refined_description="Second job...",
                relevant_skills=["Python", "AWS"],
                start_date=datetime(2020, 2, 1),
                end_date=None,
                timestamp=now + timedelta(minutes=5),
            ),
        ]

        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Looking for a senior Python developer...",
            job_analysis=None,
            refined_roles=roles,
            created_at=now,
            updated_at=now + timedelta(minutes=10),
        )

        assert len(log_entry.refined_roles) == 2
        assert log_entry.refined_roles[0].original_index == 0
        assert log_entry.refined_roles[1].original_index == 1

    def test_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            RunningLog(
                resume_id=1,
                # Missing user_id
                job_description="Looking for a Python developer...",
                job_analysis=None,
                refined_roles=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestModelExport:
    """Tests that models are properly exportable."""

    def test_models_are_importable(self) -> None:
        """Test that both models can be imported from the module."""
        # This test passes if the imports at the top of the file work
        assert RefinedRoleRecord is not None
        assert RunningLog is not None
