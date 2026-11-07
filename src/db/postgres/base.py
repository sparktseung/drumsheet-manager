from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import sqlalchemy as sa
from sqlalchemy.engine import Engine


class TableBase:
    """Generic database connection manager for Postgres tables via SQLAlchemy.

    Provides engine lifecycle management, transaction control, and lazy
    table reflection. Child classes handle SQL execution directly.

    Example:
        class SongDB(TableBase):
            def get_song(self, song_id: int):
                stmt = sa.select(self.get_table()).where(
                    self.get_table().c.id == song_id
                )
                with self.engine.begin() as conn:
                    return conn.execute(stmt).mappings().first()
    """

    def __init__(
        self,
        schema: str,
        table_name: str,
        dsn: str | None = None,
        engine: Engine | None = None,
    ) -> None:
        """Initialize database connection and table configuration.

        Params
        ------
        schema: str
            PostgreSQL schema name.
        table_name: str
            Name of the table this class manages.
        dsn: str | None
            Database connection string used when *engine* is not provided.
        engine: Engine | None
            Existing SQLAlchemy engine to reuse for shared pooling.
        """
        if engine is None and dsn is None:
            raise ValueError("Either 'engine' or 'dsn' must be provided")

        self.schema = schema
        self.table_name = table_name
        self.engine: Engine = engine or sa.create_engine(dsn, future=True)
        self._reflected_table: sa.Table | None = None

    def __enter__(self) -> TableBase:
        """Enter context manager for automatic resource cleanup."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager and dispose of database resources."""
        self.close()

    def close(self) -> None:
        """Dispose of all pooled database connections."""
        self.engine.dispose()

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for explicit transaction control.

        All statements executed within this context are committed as one
        atomic unit or rolled back on exception.
        """
        with self.engine.begin() as conn:
            yield conn

    def get_table(self) -> sa.Table:
        """Get the SQLAlchemy Table object via lazy reflection.

        On first call, connects to the database and inspects the table
        schema. Subsequent calls return the cached Table object.
        """
        if self._reflected_table is None:
            self._reflected_table = sa.Table(
                self.table_name,
                sa.MetaData(),
                schema=self.schema,
                autoload_with=self.engine,
            )
        return self._reflected_table
