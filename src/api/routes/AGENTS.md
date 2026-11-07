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

### Discovery — [discovery.py](discovery.py)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/discovery/files` | List valid song files in `SONG_DATA_STAGING_FOLDER` |
| POST | `/admin/discovery/validate` | Run all validation checks, return errors + warnings |
| POST | `/admin/discovery/insert` | Validate, insert master row, rename files, move to data folder |

**Insert pipeline**:
1. **Validate names** — checks for whitespace, boolean-like values (TRUE/FALSE), numeric strings, date-like strings, month names, formula triggers (=+-@), NUL bytes, control characters, length limits, and forbidden filename characters.
2. **Validate files** — ensures selected files exist and are within the staging folder.
3. **Validate no filename conflict** — checks that normalized file names (including local names when provided) don't already exist in the staging or data folder. Uses case-insensitive collision detection for cross-platform safety.
4. **Duplicate check** — if the artist/song pair already exists in the master spreadsheet, a **warning** is shown (not an error). The user can still proceed — files are renamed and moved, but the master row is skipped. This supports adding alternate drum sheet versions for existing songs.
5. **Insert master row** — uses openpyxl directly with `number_format="@"` (text format) to prevent Excel auto-conversion of string values. The `song_id` is not stored in the spreadsheet; it is generated deterministically by `SongMasterManager` during sync.
6. **Rename files** — renames staging files to `{normalized_stem}.{ext}`. When local names are provided, the stem becomes `{artist_local} - {song_name_local} - {artist_en} - {song_name_en}`.
7. **Move files** — moves renamed files from staging to `SONG_DATA_FOLDER`.

**Frontend flow**: The review step calls `POST /admin/discovery/validate` before showing the review screen. Errors block progression; warnings are displayed but allow the user to proceed.

## Key patterns

- All song endpoints use SQLAlchemy autoload to reflect views at request time.
- `_build_base_filters()` constructs WHERE clauses from query params.
- `_fetch_rows()` / `_fetch_count()` are shared helpers for building paginated queries.
- File endpoints look up `file_path` from `vw_all_songs`, then validate the file exists on disk before returning a `FileResponse`.
- **PRNG reseeding**: `GET /songs/playable/random` calls `SETSEED(EXTRACT(EPOCH FROM CLOCK_TIMESTAMP()))` before `ORDER BY RANDOM()` to avoid deterministic ordering from pooled connection reuse.