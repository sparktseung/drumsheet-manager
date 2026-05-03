from dotenv import load_dotenv
import os
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    DateTime,
)
from sqlalchemy.schema import CreateSchema
import sqlalchemy as sa

from src.db.postgres.song_master import (
    build_song_master_table,
)

if __name__ == "__main__":

    load_dotenv()
    dsn = os.getenv("POSTGRES_DB_DSN")
    schema = os.getenv("POSTGRES_DB_SCHEMA")

    if not dsn:
        raise ValueError("POSTGRES_DB_DSN is not set")
    # Use psycopg v3 driver when DSN is generic postgresql://
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    if not schema:
        raise ValueError("POSTGRES_DB_SCHEMA is not set")

    # Create the table in the database
    engine = sa.create_engine(dsn)

    with engine.begin() as conn:
        conn.execute(CreateSchema(schema, if_not_exists=True))

    metadata = MetaData()

    song_master_table = build_song_master_table(metadata, schema)

    song_audio_table = Table(
        "song_audio",
        metadata,
        Column(
            "song_id",
            sa.UUID,
            sa.ForeignKey(f"{schema}.song_master.song_id"),
            nullable=False,
            primary_key=True,
        ),
        Column("file_path_hash", String(64), nullable=False),
        Column("file_path", String(1024), nullable=False),
        Column("file_name", String(255), nullable=False),
        Column("stem", String(255), nullable=False),
        Column("extension", String(16), nullable=False),
        Column("file_type", String(32), nullable=False),
        Column("artist_en", String(255), nullable=False),
        Column("song_name_en", String(255), nullable=False),
        Column("last_modified_ts", DateTime, nullable=False),
        Column("created_at", DateTime, server_default=sa.func.now()),
        Column("updated_at", DateTime, server_default=sa.func.now()),
        schema=schema,
    )

    song_drum_sheet_table = Table(
        "song_drum_sheet",
        metadata,
        Column(
            "song_id",
            sa.UUID,
            sa.ForeignKey(f"{schema}.song_master.song_id"),
            nullable=False,
            primary_key=True,
        ),
        Column("file_path_hash", String(64), nullable=False),
        Column("file_path", String(1024), nullable=False),
        Column("file_name", String(255), nullable=False),
        Column("stem", String(255), nullable=False),
        Column("extension", String(16), nullable=False),
        Column("file_type", String(32), nullable=False),
        Column("artist_en", String(255), nullable=False),
        Column("song_name_en", String(255), nullable=False),
        Column("last_modified_ts", DateTime, nullable=False),
        Column("created_at", DateTime, server_default=sa.func.now()),
        Column("updated_at", DateTime, server_default=sa.func.now()),
        schema=schema,
    )

    song_source_table = Table(
        "song_source",
        metadata,
        Column(
            "song_id",
            sa.UUID,
            sa.ForeignKey(f"{schema}.song_master.song_id"),
            nullable=False,
            primary_key=True,
        ),
        Column("file_path_hash", String(64), nullable=False),
        Column("file_path", String(1024), nullable=False),
        Column("file_name", String(255), nullable=False),
        Column("stem", String(255), nullable=False),
        Column("extension", String(16), nullable=False),
        Column("file_type", String(32), nullable=False),
        Column("artist_en", String(255), nullable=False),
        Column("song_name_en", String(255), nullable=False),
        Column("last_modified_ts", DateTime, nullable=False),
        Column("created_at", DateTime, server_default=sa.func.now()),
        Column("updated_at", DateTime, server_default=sa.func.now()),
        schema=schema,
    )

    metadata.create_all(engine)
