from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

import sqlalchemy as sa
from sqlalchemy.engine import Engine

VW_ALL_SONGS = "vw_all_songs"
VW_PLAYABLE_SONGS = "vw_playable_songs"
VW_UNPLAYABLE_SONGS = "vw_unplayable_songs"
VW_RECENTLY_UPDATED_SONGS = "vw_recently_updated_songs"


class AppViewManager:
    """Manage database views used by the web application."""

    def __init__(
        self,
        dsn: str,
        schema: str,
        engine: Engine | None = None,
    ) -> None:
        self.schema = schema
        self.engine: Engine = engine or sa.create_engine(dsn, future=True)

    def __enter__(self) -> AppViewManager:
        """Support context manager usage for this view manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Always dispose resources when leaving a with block."""
        self.close()

    def create_views(self) -> None:
        """Create all application views."""
        self.create_vw_all_songs()
        self.create_vw_playable_songs()
        self.create_vw_unplayable_songs()
        self.create_vw_recently_updated_songs()

    def close(self) -> None:
        """Dispose of pooled database connections."""
        self.engine.dispose()

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager for explicit transaction control."""
        with self.engine.begin() as conn:
            yield conn

    def create_vw_all_songs(self) -> None:
        """Create vw_all_songs by full-joining song tables on song_id."""
        stmt = sa.text(f"""
            CREATE OR REPLACE VIEW {self.schema}.{VW_ALL_SONGS} AS
            SELECT
                COALESCE(
                    m.song_id,
                    a.song_id,
                    d.song_id,
                    s.song_id
                ) AS song_id,
                (m.song_id IS NOT NULL) AS in_master,
                m.artist_en,
                m.song_name_en,
                m.genre,
                m.artist_local,
                m.song_name_local,
                (
                    SELECT MAX(v.updated_at)
                    FROM (VALUES
                        (m.updated_at),
                        (a.updated_at),
                        (d.updated_at),
                        (s.updated_at)
                    ) AS v(updated_at)
                ) AS updated_at,
                (a.song_id IS NOT NULL) AS audio_available,
                a.file_path AS audio_file_path,
                (d.song_id IS NOT NULL) AS drum_sheet_available,
                d.file_path AS drum_sheet_file_path,
                (s.song_id IS NOT NULL) AS source_available,
                s.file_path AS source_file_path
            FROM {self.schema}.song_master AS m
            FULL OUTER JOIN {self.schema}.song_audio AS a
                ON a.song_id = m.song_id
            FULL OUTER JOIN {self.schema}.song_drum_sheet AS d
                ON d.song_id = COALESCE(m.song_id, a.song_id)
            FULL OUTER JOIN {self.schema}.song_source AS s
                ON s.song_id = COALESCE(m.song_id, a.song_id, d.song_id)
            """)

        with self.transaction() as conn:
            conn.execute(stmt)

    def create_vw_playable_songs(self) -> None:
        """Create vw_playable_songs from vw_all_songs.

        A playable song must have both an audio file and a drum sheet.
        """
        stmt = sa.text(f"""
            CREATE OR REPLACE VIEW {self.schema}.{VW_PLAYABLE_SONGS} AS
            SELECT
                p.song_id,
                p.in_master,
                COALESCE(p.artist_en, d.artist_en, a.artist_en) AS artist_en,
                COALESCE(
                    p.song_name_en,
                    d.song_name_en,
                    a.song_name_en
                ) AS song_name_en,
                p.genre,
                p.artist_local,
                p.song_name_local,
                p.updated_at,
                p.audio_available,
                p.audio_file_path,
                p.drum_sheet_available,
                p.drum_sheet_file_path,
                p.source_available,
                p.source_file_path
            FROM {self.schema}.{VW_ALL_SONGS} AS p
            LEFT JOIN {self.schema}.song_drum_sheet AS d
                ON d.song_id = p.song_id
            LEFT JOIN {self.schema}.song_audio AS a
                ON a.song_id = p.song_id
            WHERE p.audio_available IS TRUE
              AND p.drum_sheet_available IS TRUE
            """)

        with self.transaction() as conn:
            conn.execute(stmt)

    def create_vw_unplayable_songs(self) -> None:
        """Create vw_unplayable_songs from vw_all_songs.

        Includes songs in master that are missing either audio or drum sheet.
        """
        stmt = sa.text(f"""
            CREATE OR REPLACE VIEW {self.schema}.{VW_UNPLAYABLE_SONGS} AS
            SELECT *
            FROM {self.schema}.{VW_ALL_SONGS}
            WHERE in_master IS TRUE
              AND (
                  audio_available IS NOT TRUE
                  OR drum_sheet_available IS NOT TRUE
              )
            """)

        with self.transaction() as conn:
            conn.execute(stmt)

    def create_vw_recently_updated_songs(self) -> None:
        """Create vw_recently_updated_songs from vw_all_songs."""
        stmt = sa.text(f"""
            CREATE OR REPLACE VIEW {self.schema}.{VW_RECENTLY_UPDATED_SONGS} AS
            SELECT *
            FROM {self.schema}.{VW_ALL_SONGS}
            WHERE updated_at IS NOT NULL
            ORDER BY updated_at DESC
            """)

        with self.transaction() as conn:
            conn.execute(stmt)
