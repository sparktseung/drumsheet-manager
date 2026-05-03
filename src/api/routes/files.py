from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ..config import get_settings
from ..dependencies import get_db_connection
from ...files.audio import Audio
from ...files.drum_sheet import DrumSheet

router = APIRouter(prefix="/files", tags=["files"])

_VW_ALL_SONGS = "vw_all_songs"


def _get_song_column(
    conn: Connection,
    column: str,
    song_id: UUID,
) -> str | None:
    """Return *column* from vw_all_songs for the given *song_id*.

    Returns ``None`` if the song row does not exist; returns an empty
    string if the row exists but the column value is NULL.
    """
    schema = get_settings().schema
    stmt = sa.text(
        f"SELECT {column}"
        f" FROM {schema}.{_VW_ALL_SONGS}"
        " WHERE song_id = :song_id"
    )
    row = conn.execute(stmt, {"song_id": str(song_id)}).mappings().first()
    if row is None:
        return None
    value = row[column]
    return value if value is not None else ""


@router.get(
    "/drum-sheet/{song_id}",
    summary="Stream drum sheet PDF",
    description=(
        "Returns the drum sheet PDF for the given song, suitable for"
        " inline rendering in the browser."
    ),
)
def get_drum_sheet(
    song_id: UUID,
    conn: Connection = Depends(get_db_connection),
) -> FileResponse:
    file_path = _get_song_column(conn, "drum_sheet_file_path", song_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="No drum sheet available for this song.",
        )
    try:
        sheet = DrumSheet.load(file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Drum sheet file not found on disk.",
        )
    return FileResponse(
        path=sheet.path,
        media_type=sheet.content_type,
        filename=sheet.path.name,
    )


@router.get(
    "/audio/{song_id}",
    summary="Stream audio file",
    description=(
        "Returns the audio file for the given song. Range requests are"
        " supported so the browser <audio> element can seek freely."
    ),
)
def get_audio(
    song_id: UUID,
    conn: Connection = Depends(get_db_connection),
) -> FileResponse:
    file_path = _get_song_column(conn, "audio_file_path", song_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="No audio available for this song.",
        )
    try:
        audio = Audio.load(file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Audio file not found on disk.",
        )
    return FileResponse(
        path=audio.path,
        media_type=audio.content_type,
        filename=audio.path.name,
    )
