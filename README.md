# Drum Sheet Manager

## Expected Structure of Raw Data Folder

```
root_folder
├── song_master_list.xlsx (or .csv, .xls)
├── song_data
│   ├── (additional qualifier) - artist_en - song_name_en.mp3
│   ├── (additional qualifier) - artist_en - song_name_en.pdf
│   ├── (additional qualifier) - artist_en - song_name_en.mscz (can be missing)
```

## API Backend (FastAPI)

### Start API

```bash
python scripts/api/run_api.py
```

Environment variables:

- `POSTGRES_DB_DSN` (required)
- `POSTGRES_DB_SCHEMA` (required)
- `API_HOST` (optional, default `127.0.0.1`)
- `API_PORT` (optional, default `8000`)
- `API_RELOAD` (optional, `1` or `0`, default `1`)
- `API_CORS_ORIGINS` (optional, comma-separated list, default `http://127.0.0.1:5173,http://localhost:5173`)

### Available Endpoints

Songs endpoints:

- `GET /songs`
- `GET /songs/playable`
- `GET /songs/unplayable`
- `GET /songs/recent`

Admin sync endpoints:

- `POST /admin/sync`
- `GET /admin/sync/current`
- `GET /admin/sync/{job_id}`
- `GET /health`

Interactive docs are available at `/docs` when the API is running.