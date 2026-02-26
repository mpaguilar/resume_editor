"""Data models and parameters for LLM orchestration."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from resume_editor.app.llm.models import JobAnalysis
from resume_editor.app.models.resume.experience import Role


@dataclass
class HandleRetryDelayParams:
    """Parameters for _handle_retry_delay function.

    Attributes:
        attempt: The current attempt number (0-indexed).
        role: The role being refined.
        response_str: The LLM response string.
        error: The error that occurred.
        job_analysis: The job analysis context.
        semaphore: Optional semaphore to release during delay.
        progress_callback: Optional callback for progress updates.

    """

    attempt: int
    role: Role
    response_str: str
    error: Exception
    job_analysis: JobAnalysis
    semaphore: asyncio.Semaphore | None = None
    progress_callback: Callable[[str], Awaitable[None]] | None = None


@dataclass
class ProcessRefinementErrorParams:
    """Parameters for _process_refinement_error function.

    Attributes:
        attempt: The current attempt number (0-indexed).
        error: The error that occurred.
        role: The role being refined.
        response_str: The LLM response string.
        job_analysis: The job analysis context.
        semaphore: Optional semaphore for retry delays.
        progress_callback: Optional callback for progress updates.

    """

    attempt: int
    error: Exception
    role: Role
    response_str: str
    job_analysis: JobAnalysis
    semaphore: asyncio.Semaphore | None = None
    progress_callback: Callable[[str], Awaitable[None]] | None = None
