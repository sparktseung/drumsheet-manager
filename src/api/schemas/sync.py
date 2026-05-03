from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SyncJob(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
