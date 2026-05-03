from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from threading import Lock, Thread
from typing import Literal
from uuid import uuid4

from ...db.sync import run_sync_once
from ..config import get_settings

SyncStatus = Literal["queued", "running", "succeeded", "failed"]


@dataclass
class SyncJobRecord:
    job_id: str
    status: SyncStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


_jobs_lock = Lock()
_jobs: dict[str, SyncJobRecord] = {}
_running_job_id: str | None = None


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _run_sync_job(job_id: str) -> None:
    global _running_job_id

    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "running"
        job.started_at = _now_utc()

    try:
        settings = get_settings()

        run_sync_once(
            dsn=settings.dsn,
            schema=settings.schema,
            master_file=settings.master_file,
            song_data_folder=settings.song_data_folder,
        )
    except Exception as exc:  # noqa: BLE001
        with _jobs_lock:
            failed_job = _jobs[job_id]
            failed_job.status = "failed"
            failed_job.error = f"{type(exc).__name__}: {exc}"
            failed_job.finished_at = _now_utc()
            if _running_job_id == job_id:
                _running_job_id = None
        return

    with _jobs_lock:
        completed_job = _jobs[job_id]
        completed_job.status = "succeeded"
        completed_job.finished_at = _now_utc()
        if _running_job_id == job_id:
            _running_job_id = None


def start_sync_job() -> SyncJobRecord:
    global _running_job_id

    with _jobs_lock:
        if _running_job_id is not None:
            raise RuntimeError(_running_job_id)

        job_id = str(uuid4())
        job = SyncJobRecord(
            job_id=job_id,
            status="queued",
            created_at=_now_utc(),
        )
        _jobs[job_id] = job
        _running_job_id = job_id

    worker = Thread(
        target=_run_sync_job,
        args=(job_id,),
        daemon=True,
        name=f"sync-job-{job_id}",
    )
    worker.start()

    return job


def get_sync_job(job_id: str) -> SyncJobRecord | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None
        return replace(job)


def get_running_job() -> SyncJobRecord | None:
    with _jobs_lock:
        if _running_job_id is None:
            return None
        job = _jobs.get(_running_job_id)
        if job is None:
            return None
        return replace(job)
