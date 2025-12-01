from godbot.core.scheduler import scheduler
from datetime import datetime


def test_scheduler_add_remove():
    scheduler.add_job("test1", "interval", {"seconds": 1, "message": "hi"})

    assert "test1" in scheduler.jobs

    removed = scheduler.remove_job("test1")

    assert removed


def test_scheduler_exec_once():
    # Add one-time job scheduled in the past (will execute immediately)
    past_time = datetime(2000, 1, 1, 0, 0, 0).isoformat()
    scheduler.add_job("once1", "once", {"time": past_time, "message": "x"})

    # It should auto-remove on run loop; manually trigger executor
    scheduler._execute("once1", scheduler.jobs["once1"])

    # Job should be removed after execution
    assert "once1" not in scheduler.jobs

