from __future__ import annotations

from collections.abc import Sequence

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
import sqlalchemy as sa
from sqlalchemy.engine import Connection, RowMapping

from ..config import get_settings
from ..dependencies import get_db_connection
from ..schemas import SongRow

router = APIRouter(prefix="/songs", tags=["songs"])

VW_ALL_SONGS = "vw_all_songs"
VW_PLAYABLE_SONGS = "vw_playable_songs"
VW_UNPLAYABLE_SONGS = "vw_unplayable_songs"
VW_RECENTLY_UPDATED_SONGS = "vw_recently_updated_songs"
SONG_ORDER_BY = "artist_en NULLS LAST, song_name_en NULLS LAST"


def _build_base_where(
    *,
    q: str | None,
    genre: str | None = None,
    in_master: bool | None,
    audio_available: bool | None,
    drum_sheet_available: bool | None,
    source_available: bool | None,
) -> tuple[str, dict[str, object]]:
    conditions: list[str] = []
    params: dict[str, object] = {}

    if q:
        conditions.append("(artist_en ILIKE :q OR song_name_en ILIKE :q)")
        params["q"] = f"%{q}%"

    if genre is not None:
        conditions.append("genre ILIKE :genre")
        params["genre"] = f"%{genre}%"

    if in_master is not None:
        conditions.append("in_master = :in_master")
        params["in_master"] = in_master

    if audio_available is not None:
        conditions.append("audio_available = :audio_available")
        params["audio_available"] = audio_available

    if drum_sheet_available is not None:
        conditions.append("drum_sheet_available = :drum_sheet_available")
        params["drum_sheet_available"] = drum_sheet_available

    if source_available is not None:
        conditions.append("source_available = :source_available")
        params["source_available"] = source_available

    if not conditions:
        return "", params

    return "WHERE " + " AND ".join(conditions), params


def _fetch_rows(
    conn: Connection,
    view_name: str,
    *,
    where_clause: str,
    where_params: dict[str, object],
    limit: int,
    offset: int,
    order_by: str,
) -> Sequence[RowMapping]:
    schema = get_settings().schema
    stmt = sa.text(f"""
        SELECT *
        FROM {schema}.{view_name}
        {where_clause}
        ORDER BY {order_by}
        LIMIT :limit
        OFFSET :offset
        """)
    params = {
        **where_params,
        "limit": limit,
        "offset": offset,
    }
    return conn.execute(stmt, params).mappings().all()


@router.get(
    "",
    response_model=list[SongRow],
    summary="List all songs",
    description="Read songs from vw_all_songs with optional filtering.",
)
def get_all_songs(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    in_master: bool | None = Query(
        default=None,
        description="Filter by master presence flag.",
    ),
    audio_available: bool | None = Query(
        default=None,
        description="Filter by audio availability.",
    ),
    drum_sheet_available: bool | None = Query(
        default=None,
        description="Filter by drum sheet availability.",
    ),
    source_available: bool | None = Query(
        default=None,
        description="Filter by source availability.",
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db_connection),
) -> list[SongRow]:
    where_clause, where_params = _build_base_where(
        q=q,
        in_master=in_master,
        audio_available=audio_available,
        drum_sheet_available=drum_sheet_available,
        source_available=source_available,
    )
    rows = _fetch_rows(
        conn,
        VW_ALL_SONGS,
        where_clause=where_clause,
        where_params=where_params,
        limit=limit,
        offset=offset,
        order_by=SONG_ORDER_BY,
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/playable",
    response_model=list[SongRow],
    summary="List playable songs",
    description="Read songs from vw_playable_songs.",
)
def get_playable_songs(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    genre: str | None = Query(
        default=None,
        description="Case-insensitive substring filter on genre.",
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db_connection),
) -> list[SongRow]:
    where_clause, where_params = _build_base_where(
        q=q,
        genre=genre,
        in_master=None,
        audio_available=None,
        drum_sheet_available=None,
        source_available=None,
    )
    rows = _fetch_rows(
        conn,
        VW_PLAYABLE_SONGS,
        where_clause=where_clause,
        where_params=where_params,
        limit=limit,
        offset=offset,
        order_by=SONG_ORDER_BY,
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/unplayable",
    response_model=list[SongRow],
    summary="List unplayable songs",
    description="Read songs from vw_unplayable_songs.",
)
def get_unplayable_songs(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    missing_audio: bool | None = Query(
        default=None,
        description="Filter rows that are missing audio.",
    ),
    missing_drum_sheet: bool | None = Query(
        default=None,
        description="Filter rows that are missing drum sheet.",
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db_connection),
) -> list[SongRow]:
    where_clause, where_params = _build_base_where(
        q=q,
        in_master=None,
        audio_available=None,
        drum_sheet_available=None,
        source_available=None,
    )

    extra_conditions: list[str] = []
    if missing_audio is True:
        extra_conditions.append("audio_available IS NOT TRUE")
    elif missing_audio is False:
        extra_conditions.append("audio_available IS TRUE")

    if missing_drum_sheet is True:
        extra_conditions.append("drum_sheet_available IS NOT TRUE")
    elif missing_drum_sheet is False:
        extra_conditions.append("drum_sheet_available IS TRUE")

    if extra_conditions:
        if where_clause:
            where_clause = (
                where_clause + " AND " + " AND ".join(extra_conditions)
            )
        else:
            where_clause = "WHERE " + " AND ".join(extra_conditions)

    rows = _fetch_rows(
        conn,
        VW_UNPLAYABLE_SONGS,
        where_clause=where_clause,
        where_params=where_params,
        limit=limit,
        offset=offset,
        order_by=SONG_ORDER_BY,
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/recent",
    response_model=list[SongRow],
    summary="List recently updated songs",
    description="Read songs from vw_recently_updated_songs.",
)
def get_recently_updated_songs(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db_connection),
) -> list[SongRow]:
    where_clause, where_params = _build_base_where(
        q=q,
        in_master=None,
        audio_available=None,
        drum_sheet_available=None,
        source_available=None,
    )
    rows = _fetch_rows(
        conn,
        VW_RECENTLY_UPDATED_SONGS,
        where_clause=where_clause,
        where_params=where_params,
        limit=limit,
        offset=offset,
        order_by="updated_at DESC",
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/incomplete",
    response_model=list[SongRow],
    summary="List incomplete songs",
    description=(
        "Songs that are in master but have no audio, drum sheet,"
        " or source file synced."
    ),
)
def get_incomplete_songs(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_db_connection),
) -> list[SongRow]:
    base_where, where_params = _build_base_where(
        q=q,
        in_master=None,
        audio_available=None,
        drum_sheet_available=None,
        source_available=None,
    )
    no_files = (
        "in_master IS TRUE"
        " AND audio_available IS NOT TRUE"
        " AND drum_sheet_available IS NOT TRUE"
        " AND source_available IS NOT TRUE"
    )
    if base_where:
        where_clause = base_where + " AND " + no_files
    else:
        where_clause = "WHERE " + no_files
    rows = _fetch_rows(
        conn,
        VW_ALL_SONGS,
        where_clause=where_clause,
        where_params=where_params,
        limit=limit,
        offset=offset,
        order_by=SONG_ORDER_BY,
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/{song_id}",
    response_model=SongRow,
    summary="Get a single song by ID",
    description="Fetch metadata for one song from vw_all_songs.",
)
def get_song(
    song_id: UUID,
    conn: Connection = Depends(get_db_connection),
) -> SongRow:
    schema = get_settings().schema
    stmt = sa.text(
        f"SELECT * FROM {schema}.{VW_ALL_SONGS} WHERE song_id = :song_id"
    )
    row = conn.execute(stmt, {"song_id": str(song_id)}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    return SongRow.model_validate(dict(row))
