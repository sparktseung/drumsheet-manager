from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateSchema

from src.db.postgres import (
    AppViewManager,
    SongAudioTable,
    SongDrumSheetTable,
    SongMasterTable,
    SongSourceTable,
    build_song_audio_table,
    build_song_drum_sheet_table,
    build_song_master_table,
    build_song_source_table,
)
from src.db.song_master.constants import SONG_MASTER_LIST_UUID
from src.db.song_master.manager import SongMasterManager


def create_tables_if_not_exist(
    *,
    dsn: str,
    schema: str,
    engine: Engine | None = None,
) -> None:
    """Create the schema and all four song tables if they do not exist."""
    created_engine = engine is None
    db_engine = engine or sa.create_engine(dsn, future=True)
    try:
        with db_engine.begin() as conn:
            conn.execute(CreateSchema(schema, if_not_exists=True))

        metadata = sa.MetaData()
        build_song_master_table(metadata, schema)
        build_song_audio_table(metadata, schema)
        build_song_drum_sheet_table(metadata, schema)
        build_song_source_table(metadata, schema)
        metadata.create_all(db_engine)
    finally:
        if created_engine:
            db_engine.dispose()


def run_sync_once(
    *,
    dsn: str,
    schema: str,
    master_file: str,
    song_data_folder: str,
) -> None:
    """Synchronize song snapshot data into postgres tables and app views."""
    engine = sa.create_engine(dsn, future=True)
    try:
        create_tables_if_not_exist(dsn=dsn, schema=schema, engine=engine)

        smm = SongMasterManager(
            master_file=master_file,
            song_data_folder=song_data_folder,
            uuid_seed=SONG_MASTER_LIST_UUID,
        )
        df_song_master, df_song_audio, df_song_drum_sheet, df_song_source = (
            smm.get_all_songs_snapshot()
        )

        smt = SongMasterTable(
            schema=schema,
            table_name="song_master",
            engine=engine,
        )
        smt.merge(df_song_master)

        sat = SongAudioTable(
            schema=schema,
            table_name="song_audio",
            engine=engine,
        )
        sat.merge(df_song_audio)

        sdst = SongDrumSheetTable(
            schema=schema,
            table_name="song_drum_sheet",
            engine=engine,
        )
        sdst.merge(df_song_drum_sheet)

        sst = SongSourceTable(
            schema=schema,
            table_name="song_source",
            engine=engine,
        )
        sst.merge(df_song_source)

        avm = AppViewManager(
            dsn=dsn,
            schema=schema,
            engine=engine,
        )
        avm.create_views()
    finally:
        engine.dispose()


__all__ = ["create_tables_if_not_exist", "run_sync_once"]
