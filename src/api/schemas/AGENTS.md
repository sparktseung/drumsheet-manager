# API Schemas — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — API layer

## Models

### SongRow — [song.py](song.py)
Pydantic model for a song row from the database views.

| Field | Type | Description |
|-------|------|-------------|
| `song_id` | `UUID` | Primary key |
| `in_master` | `bool` | Whether the song exists in the master spreadsheet |
| `artist_en` | `str \| None` | Artist name in English |
| `song_name_en` | `str \| None` | Song name in English |
| `genre` | `str \| None` | Genre |
| `artist_local` | `str \| None` | Artist name in local language |
| `song_name_local` | `str \| None` | Song name in local language |
| `updated_at` | `datetime \| None` | Most recent update timestamp across all child tables |
| `audio_available` | `bool` | Whether an audio file exists |
| `audio_file_path` | `str \| None` | Path to the audio file on disk |
| `loudness_gain_db` | `float \| None` | Playback gain in dB for loudness normalization |
| `drum_sheet_available` | `bool` | Whether a drum sheet PDF exists |
| `drum_sheet_file_path` | `str \| None` | Path to the drum sheet PDF on disk |
| `source_available` | `bool` | Whether a MuseScore source file exists |
| `source_file_path` | `str \| None` | Path to the source file on disk |

### SongCount — [song.py](song.py)
| Field | Type | Description |
|-------|------|-------------|
| `total` | `int` | Total number of songs matching the current filters |

### SyncJob — [sync.py](sync.py)
| Field | Type | Description |
|-------|------|-------------|
| `job_id` | `str` | UUID string |
| `status` | `Literal["queued", "running", "succeeded", "failed"]` | Current job status |
| `created_at` | `datetime` | When the job was created |
| `started_at` | `datetime \| None` | When the job started running |
| `finished_at` | `datetime \| None` | When the job completed |
| `error` | `str \| None` | Error message if status is "failed" |