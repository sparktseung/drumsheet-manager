from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SongRow(BaseModel):
    song_id: UUID
    in_master: bool
    artist_en: str | None = None
    song_name_en: str | None = None
    genre: str | None = None
    artist_local: str | None = None
    song_name_local: str | None = None
    updated_at: datetime | None = None
    audio_available: bool
    audio_file_path: str | None = None
    drum_sheet_available: bool
    drum_sheet_file_path: str | None = None
    source_available: bool
    source_file_path: str | None = None


class SongCount(BaseModel):
    total: int
