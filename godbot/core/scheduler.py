"""
Scheduler 2.0 — Phase 11.5
----------------------------------------------------
Features:
    - Persistent jobs (jobs.json)
    - Interval jobs
    - One-time jobs
    - Cron jobs
    - Auto-reload on startup
    - Threaded execution
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional

from godbot.core.logging import get_logger

log = get_logger(__name__)


JOBS_FILE = "jobs.json"


# --------------------------------------------------------------
# Helpers
# --------------------------------------------------------------

def load_jobs() -> Dict[str, Any]:
    if not os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs: Dict[str, Any]):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4)


# --------------------------------------------------------------
# Cron Parser
# --------------------------------------------------------------

def cron_matches(cron: str, now: datetime) -> bool:
    """
    Cron format: MIN HOUR DOM MON DOW

    Supports "*" wildcards.
    
    Note: DOW in cron is 0=Sunday, 1=Monday, ..., 6=Saturday
    Python weekday() is 0=Monday, 1=Tuesday, ..., 6=Sunday
    """
    parts = cron.split()

    if len(parts) != 5:
        return False

    minute, hour, dom, mon, dow = parts

    def match(p: str, v: int) -> bool:
        return p == "*" or p == str(v)

    # Convert Python weekday (0=Mon) to cron weekday (0=Sun)
    cron_dow = (now.weekday() + 1) % 7

    return (
        match(minute, now.minute)
        and match(hour, now.hour)
        and match(dom, now.day)
        and match(mon, now.month)
        and match(dow, cron_dow)
    )


# --------------------------------------------------------------
# Scheduler
# --------------------------------------------------------------

class Scheduler:
    def __init__(self):
        self.jobs = load_jobs()
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        log.info("Scheduler started. Jobs loaded: %s", list(self.jobs.keys()))

    def stop(self):
        self.running = False
        log.info("Scheduler stopped.")

    # ----------------------------------------------------------
    # Add Job
    # ----------------------------------------------------------
    def add_job(self, job_id: str, job_type: str, data: Dict[str, Any]):
        self.jobs[job_id] = {
            "type": job_type,
            "data": data,
            "created": datetime.now().isoformat(),
        }
        save_jobs(self.jobs)
        log.info(f"Added job: {job_id}")

    # ----------------------------------------------------------
    # Remove Job
    # ----------------------------------------------------------
    def remove_job(self, job_id: str) -> bool:
        if job_id not in self.jobs:
            return False
        del self.jobs[job_id]
        save_jobs(self.jobs)
        log.info(f"Removed job: {job_id}")
        return True

    # ----------------------------------------------------------
    # Job Loop
    # ----------------------------------------------------------
    def _run_loop(self):
        while self.running:
            now = datetime.now()
            for job_id, job in list(self.jobs.items()):
                try:
                    if self._should_run_job(job, now):
                        self._execute(job_id, job)
                except Exception as e:
                    log.error(f"Error in job {job_id}: {e}", exc_info=True)
            time.sleep(1)

    # ----------------------------------------------------------
    # Job Execution
    # ----------------------------------------------------------
    def _execute(self, job_id: str, job: Dict[str, Any]):
        job_type = job["type"]
        data = job["data"]

        log.info(f"Executing job {job_id} ({job_type})")

        # For now, jobs only print messages.
        # In Phase 12+, jobs can call bot functions, LM etc.
        print(f"[JOB {job_id}] {data.get('message', '')}")

        # Remove one-time jobs
        if job_type == "once":
            self.remove_job(job_id)

    # ----------------------------------------------------------
    # Determine if job should run
    # ----------------------------------------------------------
    def _should_run_job(self, job: Dict[str, Any], now: datetime) -> bool:
        job_type = job["type"]
        data = job["data"]

        if job_type == "interval":
            last_run = data.get("last_run")

            interval = data["seconds"]

            if last_run is None:
                data["last_run"] = now.isoformat()
                save_jobs(self.jobs)
                return True

            last = datetime.fromisoformat(last_run)
            if (now - last).total_seconds() >= interval:
                data["last_run"] = now.isoformat()
                save_jobs(self.jobs)
                return True

        if job_type == "once":
            target = datetime.fromisoformat(data["time"])
            return now >= target

        if job_type == "cron":
            cron_str = data["cron"]
            return cron_matches(cron_str, now)

        return False


# Global scheduler instance
scheduler = Scheduler()
