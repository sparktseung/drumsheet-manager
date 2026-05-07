from __future__ import annotations

from typing import Any
import uuid

import polars as pl
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .base import TableBase

SONG_DRUM_SHEET_TABLE_NAME = "song_drum_sheet"
SONG_DRUM_SHEET_PRIMARY_KEY = "song_id"
SONG_DRUM_SHEET_DATA_COLUMNS = frozenset(
    {
        "file_path_hash",
        "file_path",
        "file_name",
        "stem",
        "extension",
        "file_type",
        "artist_en",
        "song_name_en",
        "last_modified_ts",
    }
)
SONG_DRUM_SHEET_TRACKING_COLUMNS = frozenset({"created_at", "updated_at"})
SONG_DRUM_SHEET_SCHEMA_COLUMNS = frozenset(
    {SONG_DRUM_SHEET_PRIMARY_KEY}
    | SONG_DRUM_SHEET_DATA_COLUMNS
    | SONG_DRUM_SHEET_TRACKING_COLUMNS
)


def build_song_drum_sheet_table(
    metadata: sa.MetaData,
    schema_name: str,
) -> sa.Table:
    """Build the song_drum_sheet SQLAlchemy table definition."""
    return sa.Table(
        SONG_DRUM_SHEET_TABLE_NAME,
        metadata,
        sa.Column(
            SONG_DRUM_SHEET_PRIMARY_KEY,
            sa.UUID,
            sa.ForeignKey(f"{schema_name}.song_master.song_id"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("file_path_hash", sa.String(64), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("stem", sa.String(255), nullable=False),
        sa.Column("extension", sa.String(16), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=False),
        sa.Column("artist_en", sa.String(255), nullable=False),
        sa.Column("song_name_en", sa.String(255), nullable=False),
        sa.Column("last_modified_ts", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema=schema_name,
    )


class SongDrumSheetTable(TableBase):
    """Table access layer for song_drum_sheet.

    Inserts and updates song drum sheet records produced by SongMasterManager.
    Merge behavior is based on primary key song_id.
    """

    def merge(self, df_incoming: pl.DataFrame) -> int:
        """Merge song drum sheet rows into the database.

        Params
        ------
        df_incoming: pl.DataFrame
            DataFrame produced by SongMasterManager that contains song drum
            sheet rows. Must include a song_id column.

        Returns
        -------
        int
            Number of affected rows reported by PostgreSQL.
        """
        if df_incoming.is_empty():
            return 0

        if SONG_DRUM_SHEET_PRIMARY_KEY not in df_incoming.columns:
            raise ValueError("df_incoming must include 'song_id'")

        table = self.get_table()

        # Keep only columns that exist in the table definition.
        allowed_columns = [
            col_name
            for col_name in df_incoming.columns
            if col_name in SONG_DRUM_SHEET_SCHEMA_COLUMNS
        ]
        if not allowed_columns:
            raise ValueError(
                "No DataFrame columns match song_drum_sheet table"
            )

        rows = df_incoming.select(allowed_columns).to_dicts()

        # Convert song_id strings to UUID objects when needed.
        for row in rows:
            song_id = row.get(SONG_DRUM_SHEET_PRIMARY_KEY)
            if song_id is None:
                raise ValueError("song_id cannot be null")
            if isinstance(song_id, str):
                row[SONG_DRUM_SHEET_PRIMARY_KEY] = uuid.UUID(song_id)

        stmt = pg_insert(table).values(rows)

        update_columns: dict[str, Any] = {
            col: stmt.excluded[col]
            for col in SONG_DRUM_SHEET_DATA_COLUMNS
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
            index_elements=[table.c[SONG_DRUM_SHEET_PRIMARY_KEY]],
            set_=update_columns,
            where=changed_condition,
        )

        with self.transaction() as conn:
            result = conn.execute(upsert_stmt)

        return max(int(result.rowcount or 0), 0)
