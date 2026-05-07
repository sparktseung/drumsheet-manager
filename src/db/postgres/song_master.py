from __future__ import annotations

from typing import Any
import uuid

import polars as pl
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import TableBase

SONG_MASTER_TABLE_NAME = "song_master"
SONG_MASTER_PRIMARY_KEY = "song_id"
SONG_MASTER_DATA_COLUMNS = frozenset(
    {
        "artist_en",
        "song_name_en",
        "genre",
        "artist_local",
        "song_name_local",
    }
)
SONG_MASTER_TRACKING_COLUMNS = frozenset({"created_at", "updated_at"})
SONG_MASTER_SCHEMA_COLUMNS = frozenset(
    {SONG_MASTER_PRIMARY_KEY}
    | SONG_MASTER_DATA_COLUMNS
    | SONG_MASTER_TRACKING_COLUMNS
)


def build_song_master_table(
    metadata: sa.MetaData,
    schema_name: str,
) -> sa.Table:
    """Build the song_master SQLAlchemy table definition."""
    return sa.Table(
        SONG_MASTER_TABLE_NAME,
        metadata,
        sa.Column(
            SONG_MASTER_PRIMARY_KEY,
            sa.UUID,
            nullable=False,
            primary_key=True,
        ),
        sa.Column("artist_en", sa.String(255), nullable=False),
        sa.Column("song_name_en", sa.String(255), nullable=False),
        sa.Column("genre", sa.String(255), nullable=True),
        sa.Column("artist_local", sa.String(255), nullable=True),
        sa.Column("song_name_local", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema=schema_name,
    )


class SongMasterTable(TableBase):
    """Table access layer for song_master.

    Inserts and updates song master records produced by SongMasterManager.
    Merge behavior is based on primary key song_id.
    """

    def merge(self, df_incoming: pl.DataFrame) -> int:
        """Merge song master rows into the database.

        Params
        ------
        df_incoming: pl.DataFrame
            DataFrame produced by SongMasterManager that contains song rows.
            Must include a song_id column.
            Always assumes the rows in the incoming dataframe conforms with
            the schema.

        Returns
        -------
        int
            Number of affected rows reported by PostgreSQL.
        """
        if df_incoming.is_empty():
            return 0

        if "song_id" not in df_incoming.columns:
            raise ValueError("df_incoming must include 'song_id'")

        table = self.get_table()

        # Keep only columns that exist in the table definition.
        allowed_columns = [
            col_name
            for col_name in df_incoming.columns
            if col_name in SONG_MASTER_SCHEMA_COLUMNS
        ]
        if not allowed_columns:
            raise ValueError("No DataFrame columns match song_master table")

        rows = df_incoming.select(allowed_columns).to_dicts()

        # Convert song_id strings to UUID objects when needed.
        for row in rows:
            song_id = row.get("song_id")
            if song_id is None:
                raise ValueError("song_id cannot be null")
            if isinstance(song_id, str):
                row["song_id"] = uuid.UUID(song_id)

        stmt = pg_insert(table).values(rows)

        update_columns: dict[str, Any] = {
            col: stmt.excluded[col]
            for col in SONG_MASTER_DATA_COLUMNS
            if col in allowed_columns
        }
        if not update_columns:
            raise ValueError("df_incoming has no updatable data columns")
        changed_condition = sa.or_(
            *(
                table.c[col].is_distinct_from(stmt.excluded[col])
                for col in update_columns
            )
        )
        update_columns["updated_at"] = sa.func.now()

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=[table.c[SONG_MASTER_PRIMARY_KEY]],
            set_=update_columns,
            where=changed_condition,
        )

        with self.transaction() as conn:
            result = conn.execute(upsert_stmt)

        return max(int(result.rowcount or 0), 0)
