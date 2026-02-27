#!/usr/bin/env python3
"""
Test Job Manager for async job tracking
"""

import pytest
from datetime import datetime, timezone, timedelta

from jesse_mcp.core.job_manager import (
    JobManager,
    JobStatus,
    Job,
    get_job_manager,
    _job_manager_instance,
)


@pytest.fixture
def job_manager():
    return JobManager()


@pytest.fixture(autouse=True)
def reset_singleton():
    global _job_manager_instance
    _job_manager_instance = None
    yield
    _job_manager_instance = None


def test_create_job(job_manager):
    job = job_manager.create_job("backtest", {"strategy": "TestStrategy"})

    assert job.id is not None
    assert len(job.id) == 8
    assert job.type == "backtest"
    assert job.status == JobStatus.PENDING
    assert job.progress_percent == 0.0
    assert job.current_step == ""
    assert job.metadata == {"strategy": "TestStrategy"}
    assert job.started_at is None
    assert job.completed_at is None
    assert job.result is None
    assert job.error is None


def test_update_progress(job_manager):
    job = job_manager.create_job("optimize")

    job_manager.update_progress(
        job.id,
        progress_percent=25.0,
        current_step="Running trial 1/100",
        iterations_completed=1,
        iterations_total=100,
    )

    updated_job = job_manager.get_job(job.id)
    assert updated_job.status == JobStatus.RUNNING
    assert updated_job.progress_percent == 25.0
    assert updated_job.current_step == "Running trial 1/100"
    assert updated_job.iterations_completed == 1
    assert updated_job.iterations_total == 100
    assert updated_job.started_at is not None


def test_update_progress_clamps_values(job_manager):
    job = job_manager.create_job("backtest")

    job_manager.update_progress(job.id, progress_percent=150.0)
    assert job_manager.get_job(job.id).progress_percent == 100.0

    job_manager.update_progress(job.id, progress_percent=-10.0)
    assert job_manager.get_job(job.id).progress_percent == 0.0


def test_get_job(job_manager):
    job = job_manager.create_job("import", {"symbol": "BTC-USDT"})

    retrieved = job_manager.get_job(job.id)
    assert retrieved is not None
    assert retrieved.id == job.id
    assert retrieved.type == "import"

    missing = job_manager.get_job("nonexistent")
    assert missing is None


def test_list_jobs(job_manager):
    job1 = job_manager.create_job("backtest")
    job2 = job_manager.create_job("optimize")
    job3 = job_manager.create_job("backtest")

    job_manager.update_progress(job1.id, progress_percent=10)
    job_manager.update_progress(job2.id, progress_percent=20)
    job_manager.update_progress(job3.id, progress_percent=30)

    all_jobs = job_manager.list_jobs()
    assert len(all_jobs) == 3

    backtest_jobs = job_manager.list_jobs(job_type="backtest")
    assert len(backtest_jobs) == 2

    optimize_jobs = job_manager.list_jobs(job_type="optimize")
    assert len(optimize_jobs) == 1

    job_manager.complete_job(job1.id, {"result": "done"})
    complete_jobs = job_manager.list_jobs(status=JobStatus.COMPLETE)
    assert len(complete_jobs) == 1
    assert complete_jobs[0].id == job1.id


def test_list_jobs_respects_limit(job_manager):
    for i in range(10):
        job_manager.create_job("backtest")

    jobs = job_manager.list_jobs(limit=5)
    assert len(jobs) == 5


def test_complete_job(job_manager):
    job = job_manager.create_job("backtest")

    job_manager.complete_job(job.id, {"total_return": 0.15, "sharpe": 1.5})

    completed = job_manager.get_job(job.id)
    assert completed.status == JobStatus.COMPLETE
    assert completed.result == {"total_return": 0.15, "sharpe": 1.5}
    assert completed.progress_percent == 100.0
    assert completed.completed_at is not None


def test_fail_job(job_manager):
    job = job_manager.create_job("backtest")

    job_manager.fail_job(job.id, "Connection timeout")

    failed = job_manager.get_job(job.id)
    assert failed.status == JobStatus.FAILED
    assert failed.error == "Connection timeout"
    assert failed.completed_at is not None


def test_cancel_job(job_manager):
    job = job_manager.create_job("optimize")

    result = job_manager.cancel_job(job.id)
    assert result is True

    cancelled = job_manager.get_job(job.id)
    assert cancelled.status == JobStatus.CANCELLED
    assert cancelled.completed_at is not None


def test_cancel_job_already_complete(job_manager):
    job = job_manager.create_job("backtest")
    job_manager.complete_job(job.id, {"result": "done"})

    result = job_manager.cancel_job(job.id)
    assert result is False

    completed = job_manager.get_job(job.id)
    assert completed.status == JobStatus.COMPLETE


def test_cancel_nonexistent_job(job_manager):
    result = job_manager.cancel_job("nonexistent")
    assert result is False


def test_job_to_dict():
    job = Job(
        id="abc12345",
        type="backtest",
        status=JobStatus.RUNNING,
        progress_percent=50.0,
        current_step="Processing",
        iterations_completed=5,
        iterations_total=10,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        completed_at=None,
        result=None,
        error=None,
        metadata={"strategy": "Test"},
    )

    d = job.to_dict()

    assert d["id"] == "abc12345"
    assert d["type"] == "backtest"
    assert d["status"] == "running"
    assert d["progress_percent"] == 50.0
    assert d["current_step"] == "Processing"
    assert d["iterations_completed"] == 5
    assert d["iterations_total"] == 10
    assert d["started_at"] == "2024-01-01T12:00:00+00:00"
    assert d["completed_at"] is None
    assert d["result"] is None
    assert d["error"] is None
    assert d["metadata"] == {"strategy": "Test"}


def test_clear_completed_jobs(job_manager):
    old_job = job_manager.create_job("backtest")
    job_manager.complete_job(old_job.id, {"result": "done"})
    old_completed = job_manager.get_job(old_job.id)
    old_completed.completed_at = datetime.now(timezone.utc) - timedelta(hours=25)

    new_job = job_manager.create_job("backtest")
    job_manager.complete_job(new_job.id, {"result": "done"})

    running_job = job_manager.create_job("backtest")
    job_manager.update_progress(running_job.id, progress_percent=50)

    removed = job_manager.clear_completed_jobs(max_age_hours=24)

    assert removed == 1
    assert job_manager.get_job(old_job.id) is None
    assert job_manager.get_job(new_job.id) is not None
    assert job_manager.get_job(running_job.id) is not None


def test_clear_completed_jobs_keeps_failed_and_cancelled(job_manager):
    failed_job = job_manager.create_job("backtest")
    job_manager.fail_job(failed_job.id, "error")
    failed = job_manager.get_job(failed_job.id)
    failed.completed_at = datetime.now(timezone.utc) - timedelta(hours=25)

    cancelled_job = job_manager.create_job("backtest")
    job_manager.cancel_job(cancelled_job.id)
    cancelled = job_manager.get_job(cancelled_job.id)
    cancelled.completed_at = datetime.now(timezone.utc) - timedelta(hours=25)

    removed = job_manager.clear_completed_jobs(max_age_hours=24)

    assert removed == 2
    assert job_manager.get_job(failed_job.id) is None
    assert job_manager.get_job(cancelled_job.id) is None


def test_singleton_pattern():
    manager1 = get_job_manager()
    manager2 = get_job_manager()

    assert manager1 is manager2


def test_update_progress_updates_metadata(job_manager):
    job = job_manager.create_job("optimize")

    job_manager.update_progress(
        job.id,
        progress_percent=10,
        best_score=1.5,
        trial_count=10,
    )

    updated = job_manager.get_job(job.id)
    assert updated.metadata["best_score"] == 1.5
    assert updated.metadata["trial_count"] == 10


def test_update_nonexistent_job_does_not_raise(job_manager):
    job_manager.update_progress("nonexistent", progress_percent=50)
    job_manager.complete_job("nonexistent", {"result": "done"})
    job_manager.fail_job("nonexistent", "error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
