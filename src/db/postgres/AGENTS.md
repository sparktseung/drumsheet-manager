# Postgres Tables — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — database layer

## Files

| File | Class/Function | Description |
|------|---------------|-------------|
| [base.py](base.py) | `TableBase` | Engine management, lazy table reflection, transaction context |
| [app_views.py](app_views.py) | `AppViewManager` | Creates/drops application views |
| [song_master.py](song_master.py) | `SongMasterTable`, `build_song_master_table` | Master song list table + upsert |
| [song_audio.py](song_audio.py) | `SongAudioTable`, `build_song_audio_table` | Audio file metadata table + upsert |
| [song_drum_sheet.py](song_drum_sheet.py) | `SongDrumSheetTable`, `build_song_drum_sheet_table` | Drum sheet metadata table + upsert |
| [song_source.py](song_source.py) | `SongSourceTable`, `build_song_source_table` | Source file metadata table + upsert |

## `TableBase` — [base.py](base.py)

Base class for all table access layers.

- **Constructor**: Takes `schema`, `table_name`, and either `dsn` or `engine`.
- **`get_table()`**: Lazy-reflects the table schema on first call, caches the result.
- **`transaction()`**: Context manager yielding a SQLAlchemy connection within a transaction.
- **`close()`**: Disposes the engine's connection pool.
- Supports `with` statement for automatic cleanup.

## Table classes (SongMasterTable, SongAudioTable, etc.)

Each extends `TableBase` and provides a `merge()` method:

1. Accepts a Polars `DataFrame` with a `song_id` column.
2. Filters columns to only those in the table schema.
3. Converts `song_id` strings to `uuid.UUID`.
4. Builds a PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` statement.
5. Only updates rows where data columns actually changed (`is_distinct_from`).
6. Returns the number of affected rows.

## `AppViewManager` — [app_views.py](app_views.py)

Manages four database views:

| View | Source | Description |
|------|--------|-------------|
| `vw_all_songs` | FULL OUTER JOIN of all four song tables | Every song known to the system |
| `vw_playable_songs` | `vw_all_songs` WHERE audio + drum sheet exist | Songs ready to play |
| `vw_unplayable_songs` | `vw_all_songs` WHERE in_master AND missing audio or drum sheet | Songs needing data |
| `vw_recently_updated_songs` | `vw_all_songs` ORDER BY updated_at DESC | Recently changed songs |

Views are created with `DROP VIEW IF EXISTS ... CASCADE` then `CREATE VIEW`.