# Database Layer — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — backend source
> **Deeper**: [postgres/](postgres/AGENTS.md), [song_master/](song_master/AGENTS.md), [sync/](sync/AGENTS.md)

## Structure

```
db/
├── postgres/       # Table definitions + AppViewManager
│   ├── base.py         # TableBase (engine, lazy reflection, transactions)
│   ├── app_views.py    # vw_all_songs, vw_playable_songs, etc.
│   ├── song_master.py  # SongMasterTable (upsert via ON CONFLICT)
│   ├── song_audio.py   # SongAudioTable
│   ├── song_drum_sheet.py
│   └── song_source.py
├── song_master/    # SongMasterManager (spreadsheet + file scan)
│   ├── manager.py      # Loads master CSV/XLSX, scans song_data_folder
│   └── constants.py    # SONG_MASTER_LIST_UUID seed
└── sync/           # Sync orchestration
    ├── runner.py       # run_sync_once, create_tables_if_not_exist
    ├── loudness.py     # FFmpeg loudnorm analysis, compute_gain_db
    └── backfill_loudness.py  # One-off backfill script
```

## Key patterns

- **Table classes** extend `TableBase` and use `merge()` with Polars DataFrames for upserts via PostgreSQL `ON CONFLICT DO UPDATE`.
- **Views** are the API query surface, created by `AppViewManager.create_views()`.
- **Sync** merges master → audio → drum_sheet → source → views in order.
- **UUIDs** are deterministic (`uuid.uuid5`) seeded from `SONG_MASTER_LIST_UUID`.
- **Loudness** uses FFmpeg `loudnorm` filter. `LOUDNESS_ALGO_VERSION` invalidates cached gains.