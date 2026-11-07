# API Routes — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — API layer

## Endpoints

### Health — [health.py](health.py)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` |

### Songs — [songs.py](songs.py)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/songs` | List all songs from `vw_all_songs` with filters |
| GET | `/songs/count` | Count all songs from `vw_all_songs` |
| GET | `/songs/playable` | List playable songs from `vw_playable_songs` |
| GET | `/songs/playable/random` | Random playable song |
| GET | `/songs/playable/count` | Count playable songs |
| GET | `/songs/unplayable` | List unplayable songs from `vw_unplayable_songs` |
| GET | `/songs/unplayable/count` | Count unplayable songs |
| GET | `/songs/recent` | Recently updated songs from `vw_recently_updated_songs` |

**Query params** (shared across most song endpoints):
- `q` — case-insensitive search on `artist_en` or `song_name_en`
- `genre` — case-insensitive substring filter (playable only)
- `in_master`, `audio_available`, `drum_sheet_available`, `source_available` — boolean filters
- `missing_audio`, `missing_drum_sheet` — boolean filters (unplayable only)
- `limit` (1–1000, default 200), `offset` (≥0)

### Files — [files.py](files.py)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/files/drum-sheet/{song_id}` | Stream drum sheet PDF |
| GET | `/files/audio/{song_id}` | Stream audio file (supports Range requests) |

### Admin — [admin.py](admin.py)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/sync` | Start a background sync job (409 if one is running) |
| GET | `/admin/sync/current` | Get currently running sync job |
| GET | `/admin/sync/{job_id}` | Get sync job status by ID |

## Key patterns

- All song endpoints use SQLAlchemy autoload to reflect views at request time.
- `_build_base_filters()` constructs WHERE clauses from query params.
- `_fetch_rows()` / `_fetch_count()` are shared helpers for building paginated queries.
- File endpoints look up `file_path` from `vw_all_songs`, then validate the file exists on disk before returning a `FileResponse`.
- **PRNG reseeding**: `GET /songs/playable/random` calls `SETSEED(EXTRACT(EPOCH FROM CLOCK_TIMESTAMP()))` before `ORDER BY RANDOM()` to avoid deterministic ordering from pooled connection reuse.