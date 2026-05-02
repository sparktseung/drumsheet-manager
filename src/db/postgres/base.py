from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import sqlalchemy as sa
from sqlalchemy.engine import Engine


class TableBase:
    """Generic database connection manager for Postgres tables via SQLAlchemy.

    Provides engine lifecycle management and transaction control.
    Child classes handle all SQL execution directly without abstraction layers.

    - Lazy table reflection: Schema is only loaded when first accessed.
    - Connection pooling: SQLAlchemy manages connection lifecycle.
    - Context manager support:
        Use with `with` statements for automatic cleanup.
    - Transaction helpers:
        Explicit `transaction()` context for atomic operations.

    Example:
        class SongDB(TableBase):
            def get_song(self, song_id: int):
                stmt = sa.select(self.get_table()).where(
                    self.get_table().c.id == song_id
                )
                with self.engine.begin() as conn:
                    return conn.execute(stmt).mappings().first()

            def insert_song(self, name: str):
                stmt = sa.insert(self.get_table()).values(name=name)
                with self.transaction() as conn:
                    return conn.execute(stmt)
    """

    def __init__(
        self,
        dsn: str,
        schema: str,
        table_name: str,
    ) -> None:
        """Initialize database connection and table configuration.

        Params
        ------
        dsn: str
            Database connection string
            (e.g., "postgresql://user:pass@localhost/db").
            SQLAlchemy will parse this to create the engine.
        schema: str
            PostgreSQL schema name (e.g., "public", "app_schema").
            Used when reflecting the table from the database.
        table_name: str
            Name of the table this class manages.
            Must exist in the specified schema.
        """
        self.schema = schema
        self.table_name = table_name
        self.engine: Engine = sa.create_engine(dsn, future=True)
        self._reflected_table: sa.Table | None = None

    def __enter__(self) -> TableBase:
        """Enter context manager for automatic resource cleanup.

        Returns:
            This TableBase instance for use in `with` statements.

        Example:
            with TableBase(dsn, schema, table) as db:
                # Use db here
                pass
            # db.close() is called automatically
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager and dispose of database resources.

        Automatically called when exiting a `with` block. Ensures all
        connections are properly closed and pooled resources are released.

        Params
        ------
        exc_type: type[BaseException] | None
            The exception type if an exception occurred, None otherwise.
        exc_val: BaseException | None
            The exception instance if an exception occurred, None otherwise.
        exc_tb: Any
            The traceback object if an exception occurred, None otherwise.
        """
        self.close()

    def close(self) -> None:
        """Close and dispose of all database connections.

        Releases all pooled connections back to the database and cleans up
        the engine. Should be called when done with the database instance.
        """
        self.engine.dispose()

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for explicit transaction control.

        Opens a database connection with automatic transaction management.
        All statements executed within this context are committed as one atomic
        unit or rolled back on exception.

        Usage:
            with db.transaction() as conn:
                conn.execute(stmt1)
                conn.execute(stmt2)  # Both succeed or both fail

        Yields:
            SQLAlchemy connection object for executing statements.
        """
        with self.engine.begin() as conn:
            yield conn

    def get_table(self) -> sa.Table:
        """Get the SQLAlchemy Table object for this class's table.

        Performs lazy reflection on first call: connects to the database and
        inspects the table schema (columns, types, constraints). Subsequent
        calls return the cached Table object.

        Returns:
            sa.Table: SQLAlchemy Table object reflecting
                the actual database schema.

        Raises:
            sqlalchemy.exc.NoSuchTableError:
                If the table doesn't exist in the schema.
        """
        if self._reflected_table is None:
            self._reflected_table = sa.Table(
                self.table_name,
                sa.MetaData(),
                schema=self.schema,
                autoload_with=self.engine,
            )
        return self._reflected_table
