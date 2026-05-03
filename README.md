# Drum Sheet Manager

- [Drum Sheet Manager](#drum-sheet-manager)
  - [Requirements](#requirements)
    - [Dependencies](#dependencies)
    - [Clone This Repo](#clone-this-repo)
    - [Set Up A PostgreSQL Database](#set-up-a-postgresql-database)
    - [Set Up Master Spreadsheet + Raw Data Folder](#set-up-master-spreadsheet--raw-data-folder)
    - [Set up Environment Variables](#set-up-environment-variables)
  - [Install Dependencies](#install-dependencies)
  - [Run The App](#run-the-app)
    - [Recommended (single command)](#recommended-single-command)
    - [Manual run (two terminals)](#manual-run-two-terminals)
  - [API Backend (FastAPI)](#api-backend-fastapi)
    - [Start API](#start-api)
    - [Available Endpoints](#available-endpoints)


## Requirements

### Dependencies
- Python 3.11+
- uv
- Node.js 20+
- npm
- PostgreSQL 18 (local instance)

### Clone This Repo

```bash
git clone https://github.com/sparktseung/drumsheet-manager
cd drumsheet-manager
```

### Set Up A PostgreSQL Database

Create a database and a user with access to that database.

Example using `psql`:

```sql
CREATE DATABASE drumsheets;
CREATE USER app_user WITH PASSWORD 'change_me';
GRANT ALL PRIVILEGES ON DATABASE drumsheets TO app_user;
```

Notes:

- The app reads from `POSTGRES_DB_DSN`.
- The app uses `POSTGRES_DB_SCHEMA` for tables/views.
- If the schema does not exist, the API now creates it automatically at startup.

### Set Up Master Spreadsheet + Raw Data Folder

- `MASTER_FILE` in `.env`: Expected Columns in Master Spreadsheet:
  - `artist_en` (required): English name of the artist/band, used for file naming and display
  - `song_name_en` (required): English name of the song, used for file naming and display
  - `genre` (optional): Genre of the song, used for filtering and display
  - `artist_local` (optional): Local language name of the artist/band, used for display
  - `song_name_local` (optional): Local language name of the song, used for display

- `SONG_DATA_FOLDER` in `.env`: Expected raw data folder structure:
    ```
    root_folder
    ├── song_master_list.xlsx (or .csv, .xls)
    ├── song_data
    │   ├── (additional qualifier) - artist_en - song_name_en.mp3
    │   ├── (additional qualifier) - artist_en - song_name_en.pdf
    │   ├── (additional qualifier) - artist_en - song_name_en.mscz (can be missing)
    ```
    `(additional qualifier)` will be ignored and are only for your file organization purposes.


### Set up Environment Variables

Create a `.env` file in the repository root.

Example:

```dotenv
# Database
POSTGRES_DB_DSN=postgresql+psycopg://app_user:change_me@localhost:5432/drumsheets
POSTGRES_DB_SCHEMA=drumsheets

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=1
API_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Frontend build/runtime
VITE_API_BASE_URL=http://localhost:8000
BACKEND_OPENAPI_URL=http://localhost:8000/openapi.json

# Raw data paths
MASTER_FILE=/absolute/path/to/root_folder/song_master_list.xlsx
SONG_DATA_FOLDER=/absolute/path/to/root_folder/song_data
```

What to change for your machine:

- `POSTGRES_DB_DSN`
- `POSTGRES_DB_SCHEMA`
- `MASTER_FILE`
- `SONG_DATA_FOLDER`

## Install Dependencies

Backend (from repo root):

```bash
uv sync
source .venv/bin/activate
```

Frontend:

```bash
cd app
npm install
cd ..
```

## Run The App

### Recommended (single command)

```bash
./start_app.sh
```

This starts both backend and frontend and prints:

- Frontend link: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`

### Manual run (two terminals)

Terminal 1 (backend):

```bash
uv run python scripts/api/run_api.py
```

Terminal 2 (frontend):

```bash
cd app
npm run dev
```

## API Backend (FastAPI)

### Start API

```bash
uv run python scripts/api/run_api.py
```

Environment variables:

- `POSTGRES_DB_DSN` (required)
- `POSTGRES_DB_SCHEMA` (required)
- `MASTER_FILE` (required)
- `SONG_DATA_FOLDER` (required)
- `API_HOST` (optional, default `127.0.0.1`)
- `API_PORT` (optional, default `8000`)
- `API_RELOAD` (optional, `1` or `0`, default `1`)
- `API_CORS_ORIGINS` (optional, comma-separated list, default `http://127.0.0.1:5173,http://localhost:5173`)

### Available Endpoints

- Songs endpoints:

  - `GET /songs`
  - `GET /songs/playable`
  - `GET /songs/unplayable`
  - `GET /songs/recent`

- Admin sync endpoints:

  - `POST /admin/sync`
  - `GET /admin/sync/current`
  - `GET /admin/sync/{job_id}`
  - `GET /health`

Interactive docs are available at `/docs` when the API is running.