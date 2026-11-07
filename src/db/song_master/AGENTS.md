# Song Master — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — database layer

## Files

| File | Description |
|------|-------------|
| [manager.py](manager.py) | `SongMasterManager` — loads master spreadsheet, scans song data folder |
| [constants.py](constants.py) | `SONG_MASTER_LIST_UUID` — seed UUID for deterministic song_id generation |

## `SongMasterManager` — [manager.py](manager.py)

Compiles a snapshot of all known songs from two sources:
1. A master spreadsheet (CSV or Excel)
2. Files on disk in the song data folder

### Constructor
- `master_file` — path to CSV/XLSX with required columns `artist_en`, `song_name_en`
- `song_data_folder` — root directory to scan for audio, drum sheet, and source files
- `uuid_seed` — seed UUID for deterministic `uuid.uuid5` generation

### `get_all_songs_snapshot()`
Returns a tuple of four Polars DataFrames:
1. `df_song_master` — rows from the spreadsheet with generated `song_id`
2. `df_song_audio` — audio files (`.mp3`, `.wav`) found on disk
3. `df_song_drum_sheet` — drum sheet files (`.pdf`) found on disk
4. `df_song_source` — source files (`.mscz`) found on disk

### `load_song_master()`
- Reads CSV (via `pl.read_csv`) or Excel (via `pl.read_excel`).
- Validates required columns exist.
- Generates a deterministic `song_id` for each row: `uuid.uuid5(seed, f"{artist_en}_{song_name_en}")`.

### `list_all_available_song_data()`
- Recursively scans `song_data_folder` for files with valid extensions.
- Extracts metadata: `file_name`, `stem`, `extension`, `last_modified_ts`, `file_path_hash` (SHA-256).
- Classifies files by type: `audio`, `drum_sheet`, or `source`.
- Parses `artist_en` and `song_name_en` from the filename stem using the convention `{anything} - {artist_en} - {song_name_en}`.
- Generates `song_id` using the same deterministic method as the master list.

### File naming convention
```
(qualifier) - artist_en - song_name_en.{mp3,pdf,mscz}
```
The qualifier prefix (everything before the second-to-last ` - ` segment) is ignored.