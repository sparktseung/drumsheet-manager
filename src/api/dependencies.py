from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine

from .config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return sa.create_engine(settings.dsn, future=True)


def close_engine() -> None:
    get_engine().dispose()


def get_db_connection() -> Generator[Connection, None, None]:
    with get_engine().begin() as conn:
        yield conn
