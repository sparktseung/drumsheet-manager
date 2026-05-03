from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
import sqlalchemy as sa
from sqlalchemy.engine import Connection, RowMapping
from sqlalchemy.sql.elements import ColumnElement

from ..config import get_settings
from ..dependencies import get_db_connection
from ..schemas import SongCount, SongRow

router = APIRouter(prefix="/songs", tags=["songs"])

VW_ALL_SONGS = "vw_all_songs"
VW_PLAYABLE_SONGS = "vw_playable_songs"
VW_UNPLAYABLE_SONGS = "vw_unplayable_songs"
VW_RECENTLY_UPDATED_SONGS = "vw_recently_updated_songs"


def _get_view(conn: Connection, view_name: str) -> sa.Table:
    schema = get_settings().schema
    return sa.Table(
        view_name,
        sa.MetaData(),
        schema=schema,
        autoload_with=conn,
    )


def _build_base_filters(
    *,
    table: sa.Table,
    q: str | None,
    genre: str | None = None,
    in_master: bool | None = None,
    audio_available: bool | None = None,
    drum_sheet_available: bool | None = None,
    source_available: bool | None = None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []

    if q:
        pattern = f"%{q}%"
        filters.append(
            sa.or_(
                table.c.artist_en.ilike(pattern),
                table.c.song_name_en.ilike(pattern),
            )
        )

    if genre is not None:
        filters.append(table.c.genre.ilike(f"%{genre}%"))

    if in_master is not None:
        filters.append(table.c.in_master.is_(in_master))

    if audio_available is not None:
        filters.append(table.c.audio_available.is_(audio_available))

    if drum_sheet_available is not None:
        filters.append(table.c.drum_sheet_available.is_(drum_sheet_available))

    if source_available is not None:
        filters.append(table.c.source_available.is_(source_available))

    return filters


def _default_song_order_by(table: sa.Table) -> tuple[ColumnElement[Any], ...]:
    return (
        table.c.artist_en.asc().nulls_last(),
        table.c.song_name_en.asc().nulls_last(),
    )


def _fetch_rows(
    conn: Connection,
    table: sa.Table,
    *,
    filters: Sequence[ColumnElement[bool]],
    limit: int,
    offset: int,
    order_by: Sequence[ColumnElement[Any]],
) -> Sequence[RowMapping]:
    stmt = sa.select(table)
    if filters:
        stmt = stmt.where(sa.and_(*filters))
    stmt = stmt.order_by(*order_by).limit(limit).offset(offset)
    return conn.execute(stmt).mappings().all()


def _fetch_count(
    conn: Connection,
    table: sa.Table,
    *,
    filters: Sequence[ColumnElement[bool]],
) -> int:
    stmt = sa.select(sa.func.count()).select_from(table)
    if filters:
        stmt = stmt.where(sa.and_(*filters))
    total = conn.execute(stmt).scalar_one()
    return int(total)


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
    table = _get_view(conn, VW_ALL_SONGS)
    filters = _build_base_filters(
        table=table,
        q=q,
        in_master=in_master,
        audio_available=audio_available,
        drum_sheet_available=drum_sheet_available,
        source_available=source_available,
    )
    rows = _fetch_rows(
        conn,
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=_default_song_order_by(table),
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/count",
    response_model=SongCount,
    summary="Count all songs",
    description="Get total count from vw_all_songs for pagination.",
)
def get_all_songs_count(
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
    conn: Connection = Depends(get_db_connection),
) -> SongCount:
    table = _get_view(conn, VW_ALL_SONGS)
    filters = _build_base_filters(
        table=table,
        q=q,
        in_master=in_master,
        audio_available=audio_available,
        drum_sheet_available=drum_sheet_available,
        source_available=source_available,
    )
    total = _fetch_count(conn, table, filters=filters)
    return SongCount(total=total)


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
    table = _get_view(conn, VW_PLAYABLE_SONGS)
    filters = _build_base_filters(
        table=table,
        q=q,
        genre=genre,
    )
    rows = _fetch_rows(
        conn,
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=_default_song_order_by(table),
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/playable/count",
    response_model=SongCount,
    summary="Count playable songs",
    description="Get total count from vw_playable_songs for pagination.",
)
def get_playable_songs_count(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    genre: str | None = Query(
        default=None,
        description="Case-insensitive substring filter on genre.",
    ),
    conn: Connection = Depends(get_db_connection),
) -> SongCount:
    table = _get_view(conn, VW_PLAYABLE_SONGS)
    filters = _build_base_filters(
        table=table,
        q=q,
        genre=genre,
    )
    total = _fetch_count(conn, table, filters=filters)
    return SongCount(total=total)


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
    table = _get_view(conn, VW_UNPLAYABLE_SONGS)
    filters = _build_base_filters(
        table=table,
        q=q,
    )

    if missing_audio is True:
        filters.append(table.c.audio_available.is_not(True))
    elif missing_audio is False:
        filters.append(table.c.audio_available.is_(True))

    if missing_drum_sheet is True:
        filters.append(table.c.drum_sheet_available.is_not(True))
    elif missing_drum_sheet is False:
        filters.append(table.c.drum_sheet_available.is_(True))

    rows = _fetch_rows(
        conn,
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=_default_song_order_by(table),
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/unplayable/count",
    response_model=SongCount,
    summary="Count unplayable songs",
    description="Get total count from vw_unplayable_songs for pagination.",
)
def get_unplayable_songs_count(
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
    conn: Connection = Depends(get_db_connection),
) -> SongCount:
    table = _get_view(conn, VW_UNPLAYABLE_SONGS)
    filters = _build_base_filters(table=table, q=q)

    if missing_audio is True:
        filters.append(table.c.audio_available.is_not(True))
    elif missing_audio is False:
        filters.append(table.c.audio_available.is_(True))

    if missing_drum_sheet is True:
        filters.append(table.c.drum_sheet_available.is_not(True))
    elif missing_drum_sheet is False:
        filters.append(table.c.drum_sheet_available.is_(True))

    total = _fetch_count(conn, table, filters=filters)
    return SongCount(total=total)


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
    table = _get_view(conn, VW_RECENTLY_UPDATED_SONGS)
    filters = _build_base_filters(table=table, q=q)
    rows = _fetch_rows(
        conn,
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=(table.c.updated_at.desc(),),
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/recent/count",
    response_model=SongCount,
    summary="Count recently updated songs",
    description=(
        "Get total count from vw_recently_updated_songs for pagination."
    ),
)
def get_recently_updated_songs_count(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    conn: Connection = Depends(get_db_connection),
) -> SongCount:
    table = _get_view(conn, VW_RECENTLY_UPDATED_SONGS)
    filters = _build_base_filters(table=table, q=q)
    total = _fetch_count(conn, table, filters=filters)
    return SongCount(total=total)


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
    table = _get_view(conn, VW_ALL_SONGS)
    filters = _build_base_filters(table=table, q=q)
    filters.extend(
        [
            table.c.in_master.is_(True),
            table.c.audio_available.is_not(True),
            table.c.drum_sheet_available.is_not(True),
            table.c.source_available.is_not(True),
        ]
    )
    rows = _fetch_rows(
        conn,
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=_default_song_order_by(table),
    )
    return [SongRow.model_validate(dict(row)) for row in rows]


@router.get(
    "/incomplete/count",
    response_model=SongCount,
    summary="Count incomplete songs",
    description="Get total count for incomplete songs pagination.",
)
def get_incomplete_songs_count(
    q: str | None = Query(
        default=None,
        description="Case-insensitive search on artist_en or song_name_en.",
    ),
    conn: Connection = Depends(get_db_connection),
) -> SongCount:
    table = _get_view(conn, VW_ALL_SONGS)
    filters = _build_base_filters(table=table, q=q)
    filters.extend(
        [
            table.c.in_master.is_(True),
            table.c.audio_available.is_not(True),
            table.c.drum_sheet_available.is_not(True),
            table.c.source_available.is_not(True),
        ]
    )
    total = _fetch_count(conn, table, filters=filters)
    return SongCount(total=total)


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
    table = _get_view(conn, VW_ALL_SONGS)
    stmt = sa.select(table).where(table.c.song_id == song_id)
    row = conn.execute(stmt).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    return SongRow.model_validate(dict(row))
