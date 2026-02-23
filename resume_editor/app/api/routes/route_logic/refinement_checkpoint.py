import logging
import threading
from datetime import datetime

from resume_editor.app.llm.models import JobAnalysis, RefinedRoleRecord, RunningLog

log = logging.getLogger(__name__)


class RunningLogManager:
    """Manages in-memory storage of refinement checkpoints.

    This class provides thread-safe access to running logs that track
    the state of resume refinement sessions. It enables failure recovery
    by allowing refinement to resume from where it left off.

    Notes:
        1. Uses an in-memory dictionary for storage with resume_id:user_id as the key.
        2. All operations are protected by a threading.Lock for thread safety.
        3. Logs are automatically timestamped when created or modified.
        4. Missing logs are handled gracefully (return None or False).

    """

    def __init__(self) -> None:
        """Initialize the manager with empty storage and a thread lock."""
        _msg = "RunningLogManager.__init__ starting"
        log.debug(_msg)
        self._storage: dict[str, RunningLog] = {}
        self._lock = threading.Lock()
        _msg = "RunningLogManager.__init__ returning"
        log.debug(_msg)

    def _make_key(self, resume_id: int, user_id: int) -> str:
        """Create a storage key from resume_id and user_id.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.

        Returns:
            str: The storage key in format "resume_id:user_id".

        Notes:
            1. Concatenates resume_id and user_id with a colon separator.

        """
        return f"{resume_id}:{user_id}"

    def create_log(
        self, resume_id: int, user_id: int, job_description: str
    ) -> RunningLog:
        """Create a new running log and store it.

        Args:
            resume_id: The ID of the resume being refined.
            user_id: The ID of the user performing the refinement.
            job_description: The job description text being targeted.

        Returns:
            RunningLog: The newly created running log.

        Notes:
            1. Creates a RunningLog with current timestamps.
            2. Stores the log in the internal storage.
            3. Thread-safe operation.

        """
        _msg = "RunningLogManager.create_log starting"
        log.debug(_msg)
        now = datetime.now()
        log_entry = RunningLog(
            resume_id=resume_id,
            user_id=user_id,
            job_description=job_description,
            created_at=now,
            updated_at=now,
        )
        key = self._make_key(resume_id, user_id)
        with self._lock:
            self._storage[key] = log_entry
        _msg = "RunningLogManager.create_log returning"
        log.debug(_msg)
        return log_entry

    def get_log(self, resume_id: int, user_id: int) -> RunningLog | None:
        """Retrieve an existing running log if present.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.

        Returns:
            RunningLog | None: The running log if found, None otherwise.

        Notes:
            1. Uses the storage key format "resume_id:user_id".
            2. Returns None if no log exists for the given IDs.
            3. Thread-safe operation.

        """
        _msg = "RunningLogManager.get_log starting"
        log.debug(_msg)
        key = self._make_key(resume_id, user_id)
        with self._lock:
            result = self._storage.get(key)
        _msg = "RunningLogManager.get_log returning"
        log.debug(_msg)
        return result

    def clear_log(self, resume_id: int, user_id: int) -> None:
        """Remove a log from storage.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.

        Notes:
            1. Uses the storage key format "resume_id:user_id".
            2. Silently succeeds if no log exists.
            3. Thread-safe operation.

        """
        _msg = "RunningLogManager.clear_log starting"
        log.debug(_msg)
        key = self._make_key(resume_id, user_id)
        with self._lock:
            self._storage.pop(key, None)
        _msg = "RunningLogManager.clear_log returning"
        log.debug(_msg)

    def add_refined_role(
        self, resume_id: int, user_id: int, role_record: RefinedRoleRecord
    ) -> None:
        """Add a refined role to the running log and update the timestamp.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.
            role_record: The refined role record to add.

        Notes:
            1. Appends the role to the refined_roles list.
            2. Updates the updated_at timestamp.
            3. Silently does nothing if no log exists.
            4. Thread-safe operation.

        """
        _msg = "RunningLogManager.add_refined_role starting"
        log.debug(_msg)
        key = self._make_key(resume_id, user_id)
        with self._lock:
            log_entry = self._storage.get(key)
            if log_entry:
                log_entry.refined_roles.append(role_record)
                log_entry.updated_at = datetime.now()
        _msg = "RunningLogManager.add_refined_role returning"
        log.debug(_msg)

    def job_description_matches(
        self, resume_id: int, user_id: int, job_description: str
    ) -> bool:
        """Check if the stored job description matches the provided one.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.
            job_description: The job description to compare against.

        Returns:
            bool: True if the stored job description matches, False otherwise.

        Notes:
            1. Returns False if no log exists for the given IDs.
            2. Performs exact string comparison.
            3. Thread-safe operation.

        """
        _msg = "RunningLogManager.job_description_matches starting"
        log.debug(_msg)
        log_entry = self.get_log(resume_id, user_id)
        if log_entry is None:
            _msg = "RunningLogManager.job_description_matches returning False (no log)"
            log.debug(_msg)
            return False
        result = log_entry.job_description == job_description
        _msg = "RunningLogManager.job_description_matches returning"
        log.debug(_msg)
        return result

    def update_job_analysis(
        self, resume_id: int, user_id: int, job_analysis: JobAnalysis
    ) -> None:
        """Store the job analysis in the running log.

        Args:
            resume_id: The ID of the resume.
            user_id: The ID of the user.
            job_analysis: The job analysis to store.

        Notes:
            1. Sets the job_analysis field on the running log.
            2. Updates the updated_at timestamp.
            3. Silently does nothing if no log exists.
            4. Thread-safe operation.

        """
        _msg = "RunningLogManager.update_job_analysis starting"
        log.debug(_msg)
        key = self._make_key(resume_id, user_id)
        with self._lock:
            log_entry = self._storage.get(key)
            if log_entry:
                log_entry.job_analysis = job_analysis
                log_entry.updated_at = datetime.now()
        _msg = "RunningLogManager.update_job_analysis returning"
        log.debug(_msg)


# Module-level singleton instance
running_log_manager = RunningLogManager()
