# API Services — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — API layer

## Services

### Sync Jobs — [sync_jobs.py](sync_jobs.py)

Manages the lifecycle of background sync jobs.

**Data structures**:
- `SyncJobRecord` — dataclass with `job_id`, `status`, `created_at`, `started_at`, `finished_at`, `error`
- `SyncStatus` — `Literal["queued", "running", "succeeded", "failed"]`

**Module-level state** (protected by `_jobs_lock`):
- `_jobs: dict[str, SyncJobRecord]` — all jobs indexed by ID
- `_running_job_id: str | None` — the currently running job (at most one)

**Functions**:
| Function | Description |
|----------|-------------|
| `start_sync_job()` | Creates a new job record, spawns a daemon thread, returns the record. Raises `RuntimeError` if a job is already running. |
| `get_sync_job(job_id)` | Returns a copy of the job record, or `None`. |
| `get_running_job()` | Returns a copy of the currently running job, or `None`. |

**Job execution** (`_run_sync_job`):
1. Sets status to `"running"`, records `started_at`.
2. Calls `run_sync_once()` from `src.db.sync`.
3. On success: sets status to `"succeeded"`, records `finished_at`.
4. On failure: sets status to `"failed"`, records error message and `finished_at`.
5. Clears `_running_job_id` in both cases.