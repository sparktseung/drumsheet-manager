from __future__ import annotations

from pydantic import BaseModel


class StagingFile(BaseModel):
    file_path: str
    file_name: str
    extension: str
    file_type: str  # "audio" | "drum_sheet" | "source"


class DiscoveryInsertRequest(BaseModel):
    artist_en: str
    song_name_en: str
    genre: str | None = None
    artist_local: str | None = None
    song_name_local: str | None = None
    audio_file_path: str | None = None
    drum_sheet_file_path: str | None = None
    source_file_path: str | None = None


class DiscoveryValidationResult(BaseModel):
    errors: list[str]
    warnings: list[str]


class DiscoveryInsertResponse(BaseModel):
    artist_en: str
    song_name_en: str
    renamed_files: list[dict[str, str]]
    moved_files: list[dict[str, str]]
    warnings: list[str]