import os
from sqlalchemy import (
    MetaData,
)
from sqlalchemy.schema import CreateSchema
import sqlalchemy as sa

from src.db.postgres import (
    build_song_master_table,
    build_song_audio_table,
    build_song_drum_sheet_table,
    build_song_source_table,
)
from src.env import load_root_dotenv

if __name__ == "__main__":
    load_root_dotenv()
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

    song_audio_table = build_song_audio_table(metadata, schema)

    song_drum_sheet_table = build_song_drum_sheet_table(metadata, schema)

    song_source_table = build_song_source_table(metadata, schema)

    metadata.create_all(engine)
