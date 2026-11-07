# API Layer — Agent Guide

> **Parent**: [../AGENTS.md](../AGENTS.md) — backend source
> **Deeper**: [routes/](routes/AGENTS.md), [schemas/](schemas/AGENTS.md), [services/](services/AGENTS.md)

## Structure

```
api/
├── config.py       # ApiSettings dataclass, env loading, DSN normalization
├── dependencies.py # SQLAlchemy engine (lru_cached), connection DI, schema bootstrap
├── main.py         # FastAPI app, CORS middleware, router registration, lifespan
├── routes/         # Endpoint modules (health, songs, files, admin)
├── schemas/        # Pydantic models (SongRow, SyncJob, SongCount)
└── services/       # Business logic (sync job lifecycle)
```

## Key patterns

- **Settings**: `get_settings()` is `@lru_cache(maxsize=1)` — loads `.env` once, normalizes DSN.
- **DB connection**: `get_db_connection()` is a FastAPI dependency yielding a SQLAlchemy `Connection` within a transaction.
- **Schema bootstrap**: `get_engine()` calls `CREATE SCHEMA IF NOT EXISTS` on first access.
- **CORS**: Origins from `API_CORS_ORIGINS` env (comma-separated), defaults to `http://[IP_ADDRESS]:5173,http://localhost:5173`.
- **Lifespan**: `close_engine()` disposes the connection pool on shutdown.