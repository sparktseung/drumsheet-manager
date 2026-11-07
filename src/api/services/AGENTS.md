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

### Validation — [validation.py](validation.py)

Comprehensive validation for song discovery insertions.

**Functions**:
| Function | Description |
|----------|-------------|
| `validate_name(value, field_label)` | Checks for whitespace, boolean-like, numeric, date-like, month-name, formula triggers, NUL bytes, control chars, length |
| `validate_filename(name, field_label)` | Checks for forbidden filesystem characters and reserved names |
| `validate_file_in_dir(file_path, allowed_dir, field_label)` | Checks file exists and is within the allowed directory |
| `validate_no_duplicate_in_master(...)` | Checks master spreadsheet for existing artist/song pair |
| `validate_normalized_filenames(...)` | Checks normalized file names don't conflict in staging or data folders. Accepts `artist_local`/`song_name_local` for stem generation. Uses case-insensitive collision detection. |

**Edge cases covered**:
- **Boolean-like**: `true`, `false`, `t`, `f`, `yes`, `no`, `on`, `off`
- **Excel errors**: `#N/A`, `#VALUE!`, `#REF!`, `#DIV/0!`, `#NUM!`, `#NAME?`, `#NULL!`, `#CALC!`, `#SPILL!`, `#FIELD!`
- **Numeric**: `123`, `-1.5`, `.5`, `1e5`, `+42`
- **Date-like**: `1/2`, `01/02`, `2024/01/01`, `1-2`
- **Month names**: `Jan`, `January`, `FEB`, etc.
- **Formula triggers**: strings starting with `=`, `+`, `-`, `@`
- **PostgreSQL**: NUL bytes (`\x00`), control characters (U+0000–U+001F except tab, LF, CR)
- **Filesystem**: `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`, reserved names `.` and `..`
- **Length**: max 255 characters (VARCHAR limit)