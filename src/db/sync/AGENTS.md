# Sync — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — database layer

## Files

| File | Description |
|------|-------------|
| [runner.py](runner.py) | `run_sync_once()`, `create_tables_if_not_exist()` — main sync orchestration |
| [loudness.py](loudness.py) | FFmpeg loudnorm analysis, `compute_gain_db()`, `LOUDNESS_ALGO_VERSION` |
| [backfill_loudness.py](backfill_loudness.py) | One-off script to populate `loudness_gain_db` for existing rows |

## `run_sync_once()` — [runner.py](runner.py)

The main sync pipeline. Called by both the API (`POST /admin/sync`) and the CLI script (`scripts/db/sync_db.py`).

### Pipeline
1. **Create tables** — `create_tables_if_not_exist()` ensures schema + all four tables exist, plus runs idempotent column migrations.
2. **Snapshot** — `SongMasterManager.get_all_songs_snapshot()` produces four DataFrames.
3. **Filter children** — `_filter_child_rows_by_master_ids()` drops audio/drum_sheet/source rows whose `song_id` doesn't appear in the master list (prevents FK violations).
4. **Merge master** — `SongMasterTable.merge()` upserts master rows.
5. **Analyze loudness** — `_add_loudness_gain_column()` computes gain for new/changed audio files, reuses cached gain for unchanged files.
6. **Merge children** — `SongAudioTable.merge()`, `SongDrumSheetTable.merge()`, `SongSourceTable.merge()`.
7. **Refresh views** — `AppViewManager.create_views()` drops and recreates all four views.

### `create_tables_if_not_exist()`
- Creates the schema via `CREATE SCHEMA IF NOT EXISTS`.
- Creates all four tables via `MetaData.create_all()`.
- Runs idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for migrations (e.g. `loudness_algo_version`).

## Loudness — [loudness.py](loudness.py)

### Constants
- `LOUDNESS_TARGET = -16` — target integrated loudness in LUFS
- `TRUE_PEAK_CEILING = -1.0` — max true peak in dBTP after gain
- `LOUDNESS_ALGO_VERSION = 2` — bump to invalidate all cached gains

### `compute_gain_db(input_i, input_tp)`
Returns `min(LOUDNESS_TARGET - input_i, TRUE_PEAK_CEILING - input_tp)`.
The clamp prevents clipping on quiet tracks with hot peaks.

### `analyze_loudness(file_path)`
Runs `ffmpeg -i <file> -af loudnorm=I=-16:print_format=json -f null -`.
Parses `input_i` and `input_tp` from the JSON in stderr.
Returns `compute_gain_db(input_i, input_tp)` or `None` on failure.

### Gain caching
`_add_loudness_gain_column()` in [runner.py](runner.py) reuses a cached gain only when:
- `file_path_hash` matches
- `last_modified_ts` matches
- `loudness_algo_version` matches `LOUDNESS_ALGO_VERSION`

## Backfill — [backfill_loudness.py](backfill_loudness.py)

One-off script for populating `loudness_gain_db` on existing rows.

```bash
uv run python -m src.db.sync.backfill_loudness         # only NULL gains
uv run python -m src.db.sync.backfill_loudness --all   # recompute every row
```

Reads `POSTGRES_DB_DSN` and `POSTGRES_DB_SCHEMA` from `.env`.