from __future__ import annotations

import json
import subprocess

import sqlalchemy as sa
import polars as pl
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

LOUDNESS_TARGET = -16  # Target integrated loudness in LUFS


def _filter_child_rows_by_master_ids(
    *,
    df_child: pl.DataFrame,
    master_song_ids: set[str],
) -> pl.DataFrame:
    """Drop child rows that do not map to any master song_id.

    Child tables use song_id as a foreign key to song_master. This filter
    prevents a bad file-name parse or missing master row from crashing the
    entire sync job.
    """
    if df_child.is_empty() or "song_id" not in df_child.columns:
        return df_child

    return df_child.filter(pl.col("song_id").is_in(list(master_song_ids)))


def _analyze_loudness(file_path: str) -> float | None:
    """Run FFmpeg loudnorm analysis on an audio file.

    Returns the target_offset (dB) needed to reach LOUDNESS_TARGET,
    or None if analysis fails.
    """
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-af", f"loudnorm=I={LOUDNESS_TARGET}:print_format=json",
        "-f", "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        stderr = result.stderr
        json_start = stderr.find("{")
        json_end = stderr.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(stderr[json_start:json_end])
            return float(data["target_offset"])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def _load_existing_gains(engine: Engine, schema: str) -> dict[str, dict]:
    stmt = sa.text(
        f"SELECT song_id, file_path_hash, last_modified_ts, loudness_gain_db"
        f" FROM {schema}.song_audio"
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    return {
        str(row["song_id"]): {
            "file_path_hash": row["file_path_hash"],
            "last_modified_ts": row["last_modified_ts"],
            "loudness_gain_db": row["loudness_gain_db"],
        }
        for row in rows
    }


def _add_loudness_gain_column(
    engine: Engine,
    schema: str,
    df_song_audio: pl.DataFrame,
) -> pl.DataFrame:
    """Add loudness_gain_db column to df_song_audio.

    New or changed files are analyzed via FFmpeg loudnorm; existing
    unchanged files keep their cached gain value from the database.
    """
    if df_song_audio.is_empty():
        return df_song_audio

    existing = _load_existing_gains(engine, schema)

    gains: list[float | None] = []
    for row in df_song_audio.to_dicts():
        song_id = row["song_id"]
        cached = existing.get(song_id)
        if (
            cached is not None
            and cached["file_path_hash"] == row["file_path_hash"]
            and cached["last_modified_ts"] == row.get("last_modified_ts")
        ):
            gains.append(cached["loudness_gain_db"])
        else:
            gain = _analyze_loudness(row["file_path"])
            gains.append(gain)

    return df_song_audio.with_columns(
        pl.Series("loudness_gain_db", gains, dtype=pl.Float32),
    )


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

        # Ensure dependent rows only reference IDs present in the master list.
        # This avoids FK violations when local filenames don't match master.
        master_song_ids = {
            str(song_id)
            for song_id in df_song_master.get_column("song_id").to_list()
        }
        df_song_audio = _filter_child_rows_by_master_ids(
            df_child=df_song_audio,
            master_song_ids=master_song_ids,
        )
        df_song_drum_sheet = _filter_child_rows_by_master_ids(
            df_child=df_song_drum_sheet,
            master_song_ids=master_song_ids,
        )
        df_song_source = _filter_child_rows_by_master_ids(
            df_child=df_song_source,
            master_song_ids=master_song_ids,
        )

        smt = SongMasterTable(
            schema=schema,
            table_name="song_master",
            engine=engine,
        )
        smt.merge(df_song_master)

        df_song_audio = _add_loudness_gain_column(
            engine=engine,
            schema=schema,
            df_song_audio=df_song_audio,
        )

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
