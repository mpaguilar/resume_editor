import logging
import threading
from datetime import datetime

import pytest
from pydantic import BaseModel

from resume_editor.app.llm.models import JobAnalysis, RunningLog, RefinedRoleRecord
from resume_editor.app.api.routes.route_logic.refinement_checkpoint import (
    RunningLogManager,
    running_log_manager,
)

log = logging.getLogger(__name__)


class TestRunningLogModels:
    """Tests for the RunningLog and RefinedRoleRecord Pydantic models."""

    def test_refined_role_record_creation(self):
        """Test that RefinedRoleRecord can be created with all fields."""
        now = datetime.now()
        record = RefinedRoleRecord(
            original_index=0,
            company="Test Company",
            title="Software Engineer",
            refined_description="Did cool things",
            relevant_skills=["Python", "FastAPI"],
            start_date=now,
            end_date=now,
            timestamp=now,
        )

        assert record.original_index == 0
        assert record.company == "Test Company"
        assert record.title == "Software Engineer"
        assert record.refined_description == "Did cool things"
        assert record.relevant_skills == ["Python", "FastAPI"]
        assert record.start_date == now
        assert record.end_date == now
        assert record.timestamp == now

    def test_running_log_creation(self):
        """Test that RunningLog can be created with required fields."""
        now = datetime.now()
        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Test job description",
            created_at=now,
            updated_at=now,
        )

        assert log_entry.resume_id == 1
        assert log_entry.user_id == 2
        assert log_entry.job_description == "Test job description"
        assert log_entry.refined_roles == []
        assert log_entry.job_analysis is None
        assert log_entry.created_at == now
        assert log_entry.updated_at == now

    def test_running_log_with_refined_roles(self):
        """Test that RunningLog can hold refined roles."""
        now = datetime.now()
        role_record = RefinedRoleRecord(
            original_index=0,
            company="Test Company",
            title="Software Engineer",
            refined_description="Did cool things",
            relevant_skills=["Python"],
            start_date=now,
            timestamp=now,
        )

        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Test job",
            refined_roles=[role_record],
            created_at=now,
            updated_at=now,
        )

        assert len(log_entry.refined_roles) == 1
        assert log_entry.refined_roles[0].company == "Test Company"

    def test_running_log_with_job_analysis(self):
        """Test that RunningLog can hold a job analysis."""
        now = datetime.now()
        job_analysis = JobAnalysis(
            key_skills=["Python", "FastAPI"],
            primary_duties=["Build APIs"],
            themes=["fast-paced"],
        )

        log_entry = RunningLog(
            resume_id=1,
            user_id=2,
            job_description="Test job",
            job_analysis=job_analysis,
            created_at=now,
            updated_at=now,
        )

        assert log_entry.job_analysis is not None
        assert log_entry.job_analysis.key_skills == ["Python", "FastAPI"]


class TestRunningLogManager:
    """Tests for the RunningLogManager class."""

    def setup_method(self):
        """Clear the manager before each test."""
        # Create a fresh manager for isolation
        self.manager = RunningLogManager()

    def test_initialization(self):
        """Test that the manager initializes with empty storage and lock."""
        assert self.manager._storage == {}
        # Verify it's a lock by checking it has acquire/release methods
        assert hasattr(self.manager._lock, "acquire")
        assert hasattr(self.manager._lock, "release")

    def test_create_log(self):
        """Test creating a new running log."""
        log_entry = self.manager.create_log(
            resume_id=1,
            user_id=2,
            job_description="Software Engineer position",
        )

        assert log_entry.resume_id == 1
        assert log_entry.user_id == 2
        assert log_entry.job_description == "Software Engineer position"
        assert log_entry.refined_roles == []
        assert isinstance(log_entry.created_at, datetime)
        assert isinstance(log_entry.updated_at, datetime)

        # Verify it's stored
        key = "1:2"
        assert key in self.manager._storage
        assert self.manager._storage[key] == log_entry

    def test_get_log_exists(self):
        """Test retrieving an existing log."""
        self.manager.create_log(1, 2, "Test job")

        retrieved = self.manager.get_log(1, 2)

        assert retrieved is not None
        assert retrieved.resume_id == 1
        assert retrieved.user_id == 2
        assert retrieved.job_description == "Test job"

    def test_get_log_not_exists(self):
        """Test retrieving a non-existent log returns None."""
        retrieved = self.manager.get_log(999, 999)
        assert retrieved is None

    def test_clear_log(self):
        """Test clearing a log removes it from storage."""
        self.manager.create_log(1, 2, "Test job")

        # Verify it exists
        assert self.manager.get_log(1, 2) is not None

        # Clear it
        self.manager.clear_log(1, 2)

        # Verify it's gone
        assert self.manager.get_log(1, 2) is None

    def test_clear_log_nonexistent(self):
        """Test clearing a non-existent log doesn't raise error."""
        # Should not raise
        self.manager.clear_log(999, 999)

    def test_add_refined_role(self):
        """Test adding a refined role to the log."""
        self.manager.create_log(1, 2, "Test job")
        now = datetime.now()

        role_record = RefinedRoleRecord(
            original_index=0,
            company="Acme Corp",
            title="Developer",
            refined_description="Built software",
            relevant_skills=["Python"],
            start_date=now,
            timestamp=now,
        )

        self.manager.add_refined_role(1, 2, role_record)

        log_entry = self.manager.get_log(1, 2)
        assert len(log_entry.refined_roles) == 1
        assert log_entry.refined_roles[0].company == "Acme Corp"

    def test_add_refined_role_multiple(self):
        """Test adding multiple refined roles."""
        self.manager.create_log(1, 2, "Test job")
        now = datetime.now()

        for i in range(3):
            role_record = RefinedRoleRecord(
                original_index=i,
                company=f"Company {i}",
                title=f"Title {i}",
                refined_description=f"Did {i} things",
                relevant_skills=["Skill"],
                start_date=now,
                timestamp=now,
            )
            self.manager.add_refined_role(1, 2, role_record)

        log_entry = self.manager.get_log(1, 2)
        assert len(log_entry.refined_roles) == 3

    def test_add_refined_role_updates_timestamp(self):
        """Test that adding a role updates the updated_at timestamp."""
        log_entry = self.manager.create_log(1, 2, "Test job")
        original_updated_at = log_entry.updated_at

        # Small delay to ensure timestamp changes
        import time

        time.sleep(0.01)

        now = datetime.now()
        role_record = RefinedRoleRecord(
            original_index=0,
            company="Acme Corp",
            title="Developer",
            refined_description="Built software",
            relevant_skills=["Python"],
            start_date=now,
            timestamp=now,
        )

        self.manager.add_refined_role(1, 2, role_record)

        updated_log = self.manager.get_log(1, 2)
        assert updated_log.updated_at > original_updated_at

    def test_job_description_matches_true(self):
        """Test job description matching returns True when matching."""
        self.manager.create_log(1, 2, "Software Engineer at Google")

        assert (
            self.manager.job_description_matches(1, 2, "Software Engineer at Google")
            is True
        )

    def test_job_description_matches_false(self):
        """Test job description matching returns False when not matching."""
        self.manager.create_log(1, 2, "Software Engineer at Google")

        assert self.manager.job_description_matches(1, 2, "Different job") is False

    def test_job_description_matches_no_log(self):
        """Test job description matching returns False when no log exists."""
        assert self.manager.job_description_matches(999, 999, "Test") is False

    def test_update_job_analysis(self):
        """Test updating job analysis in the log."""
        self.manager.create_log(1, 2, "Test job")

        job_analysis = JobAnalysis(
            key_skills=["Python", "SQL"],
            primary_duties=["Build APIs", "Write tests"],
            themes=["collaborative", "fast-paced"],
        )

        self.manager.update_job_analysis(1, 2, job_analysis)

        log_entry = self.manager.get_log(1, 2)
        assert log_entry.job_analysis is not None
        assert log_entry.job_analysis.key_skills == ["Python", "SQL"]

    def test_update_job_analysis_no_log(self):
        """Test updating job analysis when no log exists doesn't raise error."""
        job_analysis = JobAnalysis(
            key_skills=["Python"],
            primary_duties=["Build"],
            themes=["fast"],
        )

        # Should not raise
        self.manager.update_job_analysis(999, 999, job_analysis)


class TestModuleLevelSingleton:
    """Tests for the module-level singleton instance."""

    def test_singleton_exists(self):
        """Test that the module-level singleton exists and is a RunningLogManager."""
        assert isinstance(running_log_manager, RunningLogManager)


class TestThreadSafety:
    """Tests for thread safety of the RunningLogManager."""

    def test_concurrent_access(self):
        """Test that concurrent access doesn't corrupt the storage."""
        manager = RunningLogManager()
        errors = []

        def create_logs():
            try:
                for i in range(10):
                    manager.create_log(i, 1, f"Job {i}")
            except Exception as e:
                errors.append(e)

        def add_roles():
            try:
                now = datetime.now()
                for i in range(10):
                    role = RefinedRoleRecord(
                        original_index=i,
                        company=f"Company {i}",
                        title="Dev",
                        refined_description="Built stuff",
                        relevant_skills=["Python"],
                        start_date=now,
                        timestamp=now,
                    )
                    manager.add_refined_role(i, 1, role)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=create_logs)
            t2 = threading.Thread(target=add_roles)
            threads.extend([t1, t2])

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors occurred during concurrent access: {errors}"

        # Verify data integrity
        for i in range(10):
            log_entry = manager.get_log(i, 1)
            if log_entry:
                assert log_entry.resume_id == i
                assert log_entry.user_id == 1
