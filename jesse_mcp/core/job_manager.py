"""
Job Manager for Async Job Management

Provides thread-safe job tracking with progress updates for long-running operations
like backtests, optimizations, and data imports.
"""

import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger("jesse-mcp.job-manager")


class JobStatus(str, Enum):
    """Job execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """
    Represents a tracked job with progress information

    Attributes:
        id: Unique 8-character job identifier
        type: Job type (e.g., 'backtest', 'optimize', 'import')
        status: Current job status
        progress_percent: Progress as percentage (0-100)
        current_step: Description of current operation
        iterations_completed: Number of completed iterations
        iterations_total: Total iterations expected
        started_at: Job start timestamp
        completed_at: Job completion timestamp (None if not complete)
        result: Job result data (None until complete)
        error: Error message if failed (None if successful)
        metadata: Additional job metadata
    """

    id: str
    type: str
    status: JobStatus = JobStatus.PENDING
    progress_percent: float = 0.0
    current_step: str = ""
    iterations_completed: int = 0
    iterations_total: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert job to dictionary representation

        Returns:
            Dict with all job fields serialized for JSON
        """
        return {
            "id": self.id,
            "type": self.type,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
            "iterations_completed": self.iterations_completed,
            "iterations_total": self.iterations_total,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class JobManager:
    """
    Thread-safe job manager for tracking async operations

    Manages job lifecycle from creation through completion or failure.
    Provides progress tracking and status queries.

    Example:
        manager = JobManager()
        job = manager.create_job("optimize", {"strategy": "MyStrategy"})
        manager.update_progress(job.id, progress_percent=25, current_step="Running trial 1/100")
        manager.complete_job(job.id, {"sharpe": 1.5})
    """

    def __init__(self):
        """Initialize job manager with empty job store and lock"""
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        logger.info("JobManager initialized")

    def create_job(self, job_type: str, metadata: Optional[Dict[str, Any]] = None) -> Job:
        """
        Create a new job and start tracking it

        Args:
            job_type: Type of job (e.g., 'backtest', 'optimize', 'import')
            metadata: Optional metadata to attach to job

        Returns:
            Created Job instance with PENDING status
        """
        job_id = uuid4().hex[:8]
        job = Job(
            id=job_id,
            type=job_type,
            status=JobStatus.PENDING,
            metadata=metadata or {},
        )

        with self._lock:
            self._jobs[job_id] = job

        logger.info(f"Created job {job_id} (type={job_type})")
        return job

    def update_progress(
        self,
        job_id: str,
        progress_percent: Optional[float] = None,
        current_step: Optional[str] = None,
        iterations_completed: Optional[int] = None,
        iterations_total: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Update job progress information

        Args:
            job_id: Job identifier
            progress_percent: Progress as percentage (0-100)
            current_step: Description of current operation
            iterations_completed: Number of completed iterations
            iterations_total: Total iterations expected
            **kwargs: Additional fields to update in metadata
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to update unknown job {job_id}")
                return

            if job.status == JobStatus.PENDING:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now(timezone.utc)
                logger.info(f"Job {job_id} started")

            if progress_percent is not None:
                job.progress_percent = min(100.0, max(0.0, progress_percent))
            if current_step is not None:
                job.current_step = current_step
            if iterations_completed is not None:
                job.iterations_completed = iterations_completed
            if iterations_total is not None:
                job.iterations_total = iterations_total
            if kwargs:
                job.metadata.update(kwargs)

        logger.debug(f"Updated job {job_id}: {progress_percent}% - {current_step}")

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID

        Args:
            job_id: Job identifier

        Returns:
            Job instance or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> List[Job]:
        """
        List jobs with optional filtering

        Args:
            job_type: Filter by job type (optional)
            status: Filter by job status (optional)
            limit: Maximum number of jobs to return

        Returns:
            List of Job instances matching filters, sorted by creation time (newest first)
        """
        with self._lock:
            jobs = list(self._jobs.values())

        if job_type:
            jobs = [j for j in jobs if j.type == job_type]
        if status:
            jobs = [j for j in jobs if j.status == status]

        jobs.sort(key=lambda j: j.started_at or datetime.min, reverse=True)
        return jobs[:limit]

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """
        Mark job as complete with result

        Args:
            job_id: Job identifier
            result: Job result data
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to complete unknown job {job_id}")
                return

            job.status = JobStatus.COMPLETE
            job.result = result
            job.progress_percent = 100.0
            job.completed_at = datetime.now(timezone.utc)

        logger.info(f"✅ Job {job_id} completed")

    def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark job as failed with error message

        Args:
            job_id: Job identifier
            error: Error message describing failure
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to fail unknown job {job_id}")
                return

            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(timezone.utc)

        logger.error(f"❌ Job {job_id} failed: {error}")

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job

        Args:
            job_id: Job identifier

        Returns:
            True if job was cancelled, False if not found or already complete
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Attempted to cancel unknown job {job_id}")
                return False

            if job.status in (JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED):
                logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
                return False

            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)

        logger.info(f"🚫 Job {job_id} cancelled")
        return True

    def clear_completed_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove completed/failed/cancelled jobs older than specified age

        Args:
            max_age_hours: Maximum age in hours for completed jobs

        Returns:
            Number of jobs removed
        """
        cutoff = datetime.now(timezone.utc)
        removed = 0

        with self._lock:
            to_remove = []
            for job_id, job in self._jobs.items():
                if job.status in (JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED):
                    if job.completed_at:
                        age_hours = (cutoff - job.completed_at).total_seconds() / 3600
                        if age_hours > max_age_hours:
                            to_remove.append(job_id)

            for job_id in to_remove:
                del self._jobs[job_id]
                removed += 1

        if removed:
            logger.info(f"Cleared {removed} old completed jobs")

        return removed


_job_manager_instance: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """
    Get singleton JobManager instance

    Returns:
        JobManager instance
    """
    global _job_manager_instance
    if _job_manager_instance is None:
        _job_manager_instance = JobManager()
    return _job_manager_instance
