from dotenv import load_dotenv
import os
from src.db.sync import run_sync_once

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

    master_file = os.getenv("MASTER_FILE")
    song_data_folder = os.getenv("SONG_DATA_FOLDER")
    if not master_file:
        raise ValueError("MASTER_FILE is not set")
    if not song_data_folder:
        raise ValueError("SONG_DATA_FOLDER is not set")

    run_sync_once(
        dsn=dsn,
        schema=schema,
        master_file=master_file,
        song_data_folder=song_data_folder,
    )
