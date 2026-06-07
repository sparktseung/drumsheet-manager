# Drumsheet Manager — Agent Guide

## Stack
- **Backend**: Python 3.11+ with FastAPI, SQLAlchemy, Polars, uv
- **Frontend**: React 19, TypeScript 5.9, Vite 8, react-router-dom, react-pdf
- **DB**: PostgreSQL 18 (local)

## Commands

### Backend (repo root)
```bash
uv sync                           # install deps
uv run python scripts/api/run_api.py   # start dev server (default :8000)
uv run python scripts/db/init_db.py    # create DB schema/tables
uv run python scripts/db/sync_db.py    # one-shot sync from spreadsheet + files
uv run python -m src.db.sync.backfill_loudness  # backfill gain for existing rows
ruff check .                       # lint (line-length=79)
```

### Frontend (app/)
```bash
npm install
npm run dev          # fetches OpenAPI types, then starts Vite (:5173)
npm run build        # fetches OpenAPI types, typechecks, builds
npm run lint         # eslint
```

### Full stack
```bash
./start_app.sh       # starts backend + frontend, prints URLs
```

## Quirks

- **OpenAPI types**: `npm run dev` and `npm run build` auto-fetch from `BACKEND_OPENAPI_URL` (default `http://localhost:8000/openapi.json`). Backend must be running.
- **DB DSN**: `postgresql://` is auto-normalized to `postgresql+psycopg://` at runtime. Keep `.env` DSN without the `+psycopg` suffix.
- **Schema**: The API creates `POSTGRES_DB_SCHEMA` at startup via `CREATE SCHEMA IF NOT EXISTS`. No manual init needed.
- **Sync**: Runs in a background daemon thread via `POST /admin/sync`. One job at a time (409 if busy). Requires `MASTER_FILE` (xlsx/csv) and `SONG_DATA_FOLDER`.
- **FFmpeg**: Required at runtime for loudness normalization (called via subprocess).
- **.env** lives at repo root, loaded automatically by backend and Vite (`envDir: '..'`).
- **react-pdf** uses `pdfjs-dist` worker loaded from `import.meta.url` — no extra config needed.

## Known patterns

- Views (`vw_all_songs`, `vw_playable_songs`, etc.) are the main API query surface, backed by SQLAlchemy autoload.
- Song tables: `song_master`, `song_audio`, `song_drum_sheet`, `song_source`, all under `POSTGRES_DB_SCHEMA`.
- Child rows (audio, drum sheets, sources) are filtered to only reference master `song_id`s during sync — avoids FK violations from unmatched filenames.
- File naming convention: `(qualifier) - artist_en - song_name_en.{mp3,pdf,mscz}`. The qualifier prefix is ignored.
- TypeScript uses `verbatimModuleSyntax`, `noUnusedLocals`, `noUnusedParameters` — strict imports and no unused vars.
