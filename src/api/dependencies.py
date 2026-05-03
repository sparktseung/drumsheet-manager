from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.schema import CreateSchema

from .config import get_settings


def _ensure_schema_exists(engine: Engine, schema: str) -> None:
    with engine.begin() as conn:
        conn.execute(CreateSchema(schema, if_not_exists=True))


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    engine = sa.create_engine(settings.dsn, future=True)
    _ensure_schema_exists(engine, settings.schema)
    return engine


def close_engine() -> None:
    get_engine().dispose()


def get_db_connection() -> Generator[Connection, None, None]:
    with get_engine().begin() as conn:
        yield conn
