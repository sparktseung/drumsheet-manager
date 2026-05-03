from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from ..env import load_root_dotenv


@dataclass(frozen=True)
class ApiSettings:
    dsn: str
    schema: str
    cors_origins: tuple[str, ...]


def _normalize_dsn(dsn: str) -> str:
    # Use psycopg v3 driver when DSN is generic postgresql://
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    return dsn


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    load_root_dotenv()

    dsn = os.getenv("POSTGRES_DB_DSN")
    schema = os.getenv("POSTGRES_DB_SCHEMA")
    cors_origins_value = os.getenv(
        "API_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )

    if not dsn:
        raise ValueError("POSTGRES_DB_DSN is not set")
    if not schema:
        raise ValueError("POSTGRES_DB_SCHEMA is not set")

    cors_origins = tuple(
        origin.strip()
        for origin in cors_origins_value.split(",")
        if origin.strip()
    )

    return ApiSettings(
        dsn=_normalize_dsn(dsn),
        schema=schema,
        cors_origins=cors_origins,
    )
