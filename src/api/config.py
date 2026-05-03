from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class ApiSettings:
    dsn: str
    schema: str


def _normalize_dsn(dsn: str) -> str:
    # Use psycopg v3 driver when DSN is generic postgresql://
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    return dsn


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    load_dotenv()

    dsn = os.getenv("POSTGRES_DB_DSN")
    schema = os.getenv("POSTGRES_DB_SCHEMA")

    if not dsn:
        raise ValueError("POSTGRES_DB_DSN is not set")
    if not schema:
        raise ValueError("POSTGRES_DB_SCHEMA is not set")

    return ApiSettings(dsn=_normalize_dsn(dsn), schema=schema)
