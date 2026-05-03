from dotenv import load_dotenv
import os
from src.db.song_master.manager import SongMasterManager
from src.db.song_master.constants import SONG_MASTER_LIST_UUID
from src.db.postgres import SongMasterTable, SongAudioTable

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

    smm = SongMasterManager(
        master_file=os.getenv("MASTER_FILE"),
        song_data_folder=os.getenv("SONG_DATA_FOLDER"),
        uuid_seed=SONG_MASTER_LIST_UUID,
    )
    df_song_master, df_song_audio, df_song_drum_sheet, df_song_source = (
        smm.get_all_songs_snapshot()
    )

    smt = SongMasterTable(
        dsn=dsn,
        schema=schema,
        table_name="song_master",
    )
    smt.merge(df_song_master)

    sat = SongAudioTable(
        dsn=dsn,
        schema=schema,
        table_name="song_audio",
    )
    sat.merge(df_song_audio)
