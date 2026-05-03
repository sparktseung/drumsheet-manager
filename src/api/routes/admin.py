from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..schemas.sync import SyncJob
from ..services.sync_jobs import get_running_job, get_sync_job, start_sync_job

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/sync",
    response_model=SyncJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a song sync job",
    description=(
        "Starts a background sync that updates tables and refreshes views."
    ),
)
def start_sync() -> SyncJob:
    try:
        job = start_sync_job()
    except RuntimeError as exc:
        running_job_id = str(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A sync job is already running. "
                f"running_job_id={running_job_id}"
            ),
        )

    return SyncJob.model_validate(job.__dict__)


@router.get(
    "/sync/current",
    response_model=SyncJob | None,
    summary="Get currently running sync job",
)
def current_sync() -> SyncJob | None:
    job = get_running_job()
    if job is None:
        return None
    return SyncJob.model_validate(job.__dict__)


@router.get(
    "/sync/{job_id}",
    response_model=SyncJob,
    summary="Get sync job status",
)
def get_sync_status(job_id: str) -> SyncJob:
    job = get_sync_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Sync job not found.")
    return SyncJob.model_validate(job.__dict__)
