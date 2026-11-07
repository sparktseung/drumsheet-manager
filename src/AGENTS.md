# Backend — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — repo root
> **Deeper**: [api/](api/AGENTS.md), [db/](db/AGENTS.md), [files/](files/AGENTS.md)

## Structure

```
src/
├── api/            # FastAPI application
│   ├── config.py       # ApiSettings dataclass, env loading
│   ├── dependencies.py # SQLAlchemy engine, connection DI
│   ├── main.py         # FastAPI app, CORS, router registration
│   ├── routes/         # health, songs, files, admin endpoints
│   ├── schemas/        # Pydantic models (SongRow, SyncJob, SongCount)
│   └── services/       # sync_jobs (background thread runner)
├── db/
│   ├── postgres/       # Table definitions + AppViewManager
│   │   ├── base.py         # TableBase (engine, lazy reflection, transactions)
│   │   ├── app_views.py    # vw_all_songs, vw_playable_songs, etc.
│   │   ├── song_master.py  # SongMasterTable (upsert via ON CONFLICT)
│   │   ├── song_audio.py   # SongAudioTable
│   │   ├── song_drum_sheet.py
│   │   └── song_source.py
│   ├── song_master/    # SongMasterManager (spreadsheet + file scan)
│   │   ├── manager.py      # Loads master CSV/XLSX, scans song_data_folder
│   │   └── constants.py    # SONG_MASTER_LIST_UUID seed
│   └── sync/           # Sync orchestration
│       ├── runner.py       # run_sync_once, create_tables_if_not_exist
│       ├── loudness.py     # FFmpeg loudnorm analysis, compute_gain_db
│       └── backfill_loudness.py  # One-off backfill script
├── files/           # Audio + DrumSheet file wrappers
│   ├── audio.py
│   └── drum_sheet.py
└── env.py           # dotenv loader, repo root resolver
```

## Key patterns

- **Table classes** (`SongMasterTable`, `SongAudioTable`, etc.) extend `TableBase` and use `merge()` with Polars DataFrames for upserts.
- **Views** (`vw_all_songs`, `vw_playable_songs`, etc.) are the API query surface, created by `AppViewManager.create_views()`.
- **Sync** runs as a daemon thread via `POST /admin/sync`. One job at a time (409 if busy). The runner merges master → audio → drum_sheet → source → views.
- **Loudness** is computed via FFmpeg `loudnorm` filter. `LOUDNESS_ALGO_VERSION` invalidates cached gains when the algorithm changes.
- **UUIDs** are deterministic (`uuid.uuid5`) seeded from `SONG_MASTER_LIST_UUID` using `artist_en` + `song_name_en`.
- **File naming**: `(qualifier) - artist_en - song_name_en.{mp3,pdf,mscz}`. The qualifier prefix is ignored.
- **DB DSN**: `postgresql://` is auto-normalized to `postgresql+psycopg://` at runtime.