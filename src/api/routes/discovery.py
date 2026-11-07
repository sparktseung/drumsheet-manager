from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
import openpyxl

from ..config import get_settings
from ..schemas.discovery import (
    DiscoveryInsertRequest,
    DiscoveryInsertResponse,
    DiscoveryValidationResult,
    StagingFile,
)
from ..services.validation import (
    validate_file_in_dir,
    validate_filename,
    validate_name,
    validate_no_duplicate_in_master,
    validate_normalized_filenames,
)
from ...db.song_master.constants import (
    AUDIO_EXTENSIONS,
    DRUM_SHEET_EXTENSIONS,
    SOURCE_EXTENSIONS,
    VALID_EXTENSIONS,
)

router = APIRouter(prefix="/admin/discovery", tags=["discovery"])


def _classify_file(ext: str) -> str:
    ext_lower = ext.lower()
    if ext_lower in AUDIO_EXTENSIONS:
        return "audio"
    if ext_lower in DRUM_SHEET_EXTENSIONS:
        return "drum_sheet"
    if ext_lower in SOURCE_EXTENSIONS:
        return "source"
    return "unknown"


def _normalized_stem(
    artist_en: str,
    song_name_en: str,
    artist_local: str | None = None,
    song_name_local: str | None = None,
) -> str:
    """Return the normalized file stem.

    When local names are provided they are prepended as a qualifier
    prefix so the sync parser still extracts artist_en/song_name_en
    from the last two segments.
    """
    if artist_local and song_name_local:
        return (
            f"{artist_local} - {song_name_local}"
            f" - {artist_en} - {song_name_en}"
        )
    return f"{artist_en} - {song_name_en}"


@router.get(
    "/files",
    response_model=list[StagingFile],
    summary="List staging files",
    description="List all valid song files in the staging folder.",
)
def list_staging_files() -> list[StagingFile]:
    settings = get_settings()
    staging_root = Path(settings.song_data_staging_folder)

    if not staging_root.exists():
        return []

    files: list[StagingFile] = []
    for file_path in staging_root.rglob("*"):
        if not file_path.is_file():
            continue
        ext = file_path.suffix.lower()
        if ext not in VALID_EXTENSIONS:
            continue
        files.append(
            StagingFile(
                file_path=str(file_path),
                file_name=file_path.name,
                extension=ext,
                file_type=_classify_file(ext),
            )
        )

    files.sort(key=lambda f: (f.file_type, f.file_name))
    return files


@router.post(
    "/validate",
    response_model=DiscoveryValidationResult,
    summary="Validate a pending song insertion",
    description=(
        "Run all validation checks and return errors and warnings."
        " Warnings (e.g. duplicate in master) do not block insertion."
    ),
)
def validate_discovery(
    body: DiscoveryInsertRequest,
) -> DiscoveryValidationResult:
    settings = get_settings()
    artist_en = body.artist_en.strip()
    song_name_en = body.song_name_en.strip()

    errors: list[str] = []
    warnings: list[str] = []

    # ── Validate names ──
    errors.extend(validate_name(artist_en, "artist_en"))
    errors.extend(validate_name(song_name_en, "song_name_en"))
    if body.artist_local:
        errors.extend(
            validate_name(body.artist_local, "artist_local")
        )
    if body.song_name_local:
        errors.extend(
            validate_name(body.song_name_local, "song_name_local")
        )
    if body.genre:
        errors.extend(validate_name(body.genre, "genre"))
    errors.extend(validate_filename(artist_en, "artist_en"))
    errors.extend(validate_filename(song_name_en, "song_name_en"))

    # ── Validate files ──
    staging = settings.song_data_staging_folder
    for label, path in [
        ("audio_file_path", body.audio_file_path),
        ("drum_sheet_file_path", body.drum_sheet_file_path),
        ("source_file_path", body.source_file_path),
    ]:
        if path:
            errors.extend(
                validate_file_in_dir(path, staging, label)
            )

    # ── Duplicate in master (warning, not error) ──
    dup_warnings = validate_no_duplicate_in_master(
        master_file=settings.master_file,
        artist_en=artist_en,
        song_name_en=song_name_en,
    )
    warnings.extend(dup_warnings)

    # ── Filename conflicts in staging / data folders ──
    extensions: list[str] = []
    if body.audio_file_path:
        extensions.append(Path(body.audio_file_path).suffix)
    if body.drum_sheet_file_path:
        extensions.append(Path(body.drum_sheet_file_path).suffix)
    if body.source_file_path:
        extensions.append(Path(body.source_file_path).suffix)

    conflict_errors = validate_normalized_filenames(
        artist_en=artist_en,
        song_name_en=song_name_en,
        artist_local=(
            body.artist_local.strip() if body.artist_local else None
        ),
        song_name_local=(
            body.song_name_local.strip()
            if body.song_name_local
            else None
        ),
        extensions=extensions,
        staging_folder=settings.song_data_staging_folder,
        data_folder=settings.song_data_folder,
    )
    errors.extend(conflict_errors)

    return DiscoveryValidationResult(
        errors=errors,
        warnings=warnings,
    )


@router.post(
    "/insert",
    response_model=DiscoveryInsertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Insert a discovered song",
    description=(
        "Validate, insert into master spreadsheet, rename files,"
        " and move them to the song data folder."
    ),
)
def insert_discovered_song(
    body: DiscoveryInsertRequest,
) -> DiscoveryInsertResponse:
    settings = get_settings()
    artist_en = body.artist_en.strip()
    song_name_en = body.song_name_en.strip()

    # ── Validate names ──
    name_errors: list[str] = []
    name_errors.extend(validate_name(artist_en, "artist_en"))
    name_errors.extend(validate_name(song_name_en, "song_name_en"))
    if body.artist_local:
        name_errors.extend(
            validate_name(body.artist_local, "artist_local")
        )
    if body.song_name_local:
        name_errors.extend(
            validate_name(body.song_name_local, "song_name_local")
        )
    if body.genre:
        name_errors.extend(validate_name(body.genre, "genre"))

    # Validate that names are safe for file names.
    name_errors.extend(validate_filename(artist_en, "artist_en"))
    name_errors.extend(validate_filename(song_name_en, "song_name_en"))

    if name_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": name_errors},
        )

    # ── Validate files ──
    file_errors: list[str] = []
    staging = settings.song_data_staging_folder
    for label, path in [
        ("audio_file_path", body.audio_file_path),
        ("drum_sheet_file_path", body.drum_sheet_file_path),
        ("source_file_path", body.source_file_path),
    ]:
        if path:
            file_errors.extend(
                validate_file_in_dir(path, staging, label)
            )

    if file_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"validation_errors": file_errors},
        )

    # ── Duplicate in master (warning, not blocking) ──
    dup_warnings = validate_no_duplicate_in_master(
        master_file=settings.master_file,
        artist_en=artist_en,
        song_name_en=song_name_en,
    )

    # ── Validate normalized file names won't conflict ──
    extensions: list[str] = []
    if body.audio_file_path:
        extensions.append(Path(body.audio_file_path).suffix)
    if body.drum_sheet_file_path:
        extensions.append(Path(body.drum_sheet_file_path).suffix)
    if body.source_file_path:
        extensions.append(Path(body.source_file_path).suffix)

    conflict_errors = validate_normalized_filenames(
        artist_en=artist_en,
        song_name_en=song_name_en,
        artist_local=(
            body.artist_local.strip() if body.artist_local else None
        ),
        song_name_local=(
            body.song_name_local.strip()
            if body.song_name_local
            else None
        ),
        extensions=extensions,
        staging_folder=settings.song_data_staging_folder,
        data_folder=settings.song_data_folder,
    )
    if conflict_errors:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"validation_errors": conflict_errors},
        )

    # ── Insert into master spreadsheet ──
    _insert_master_row(
        master_file=settings.master_file,
        artist_en=artist_en,
        song_name_en=song_name_en,
        genre=body.genre.strip() if body.genre else None,
        artist_local=(
            body.artist_local.strip() if body.artist_local else None
        ),
        song_name_local=(
            body.song_name_local.strip()
            if body.song_name_local
            else None
        ),
    )

    # ── Rename files ──
    renamed = _rename_staging_files(
        body=body,
        artist_en=artist_en,
        song_name_en=song_name_en,
        staging_folder=settings.song_data_staging_folder,
    )

    # ── Move files ──
    moved = _move_files_to_data_folder(
        renamed=renamed,
        data_folder=settings.song_data_folder,
    )

    return DiscoveryInsertResponse(
        artist_en=artist_en,
        song_name_en=song_name_en,
        renamed_files=renamed,
        moved_files=moved,
        warnings=dup_warnings,
    )


def _insert_master_row(
    *,
    master_file: str,
    artist_en: str,
    song_name_en: str,
    genre: str | None,
    artist_local: str | None,
    song_name_local: str | None,
) -> None:
    """Insert a new row into the master spreadsheet using openpyxl.

    Uses openpyxl directly (not Polars write_excel) to ensure string
    values are written as text cells, preventing Excel from
    auto-converting boolean-like, numeric, or date-like values.
    """
    master_path = Path(master_file)
    if not master_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Master file not found: {master_file}",
        )

    try:
        wb = openpyxl.load_workbook(master_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read master file: {exc}",
        )

    ws = wb.active
    if ws is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Master file has no active worksheet",
        )

    # Find the next empty row.
    next_row = ws.max_row + 1

    # Build a column-name → column-index map from the header row.
    col_map: dict[str, int] = {}
    for col_idx in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col_idx).value
        if header is not None:
            col_map[str(header).strip().lower()] = col_idx

    # Write values as text cells to prevent auto-conversion.
    def _set_cell(col_name: str, value: str | None) -> None:
        idx = col_map.get(col_name.lower())
        if idx is None:
            return
        cell = ws.cell(row=next_row, column=idx)
        if value is not None:
            cell.value = value
            cell.number_format = "@"  # Text format

    _set_cell("artist_en", artist_en)
    _set_cell("song_name_en", song_name_en)
    _set_cell("genre", genre)
    _set_cell("artist_local", artist_local)
    _set_cell("song_name_local", song_name_local)

    try:
        wb.save(master_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write master file: {exc}",
        )
    finally:
        wb.close()


def _rename_staging_files(
    *,
    body: DiscoveryInsertRequest,
    artist_en: str,
    song_name_en: str,
    staging_folder: str,
) -> list[dict[str, str]]:
    """Rename staging files to the normalized naming convention."""
    normalized_stem = _normalized_stem(
        artist_en=artist_en,
        song_name_en=song_name_en,
        artist_local=(
            body.artist_local.strip() if body.artist_local else None
        ),
        song_name_local=(
            body.song_name_local.strip() if body.song_name_local else None
        ),
    )
    staging_root = Path(staging_folder)

    file_map: list[tuple[str, str | None]] = [
        ("audio", body.audio_file_path),
        ("drum_sheet", body.drum_sheet_file_path),
        ("source", body.source_file_path),
    ]

    renamed: list[dict[str, str]] = []
    for file_type, old_path_str in file_map:
        if old_path_str is None:
            continue
        old_path = Path(old_path_str)
        new_name = f"{normalized_stem}{old_path.suffix}"
        new_path = staging_root / new_name

        if new_path.exists() and new_path != old_path:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot rename '{old_path.name}' to"
                    f" '{new_name}': target already exists"
                ),
            )

        old_path.rename(new_path)
        renamed.append(
            {
                "file_type": file_type,
                "old_name": old_path.name,
                "new_name": new_name,
                "new_path": str(new_path),
            }
        )

    return renamed


def _move_files_to_data_folder(
    *,
    renamed: list[dict[str, str]],
    data_folder: str,
) -> list[dict[str, str]]:
    """Move renamed files from staging to the song data folder."""
    data_root = Path(data_folder)
    data_root.mkdir(parents=True, exist_ok=True)

    moved: list[dict[str, str]] = []
    for entry in renamed:
        src = Path(entry["new_path"])
        dst = data_root / entry["new_name"]

        if dst.exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot move '{entry['new_name']}' to"
                    f" '{data_folder}': target already exists"
                ),
            )

        shutil.move(str(src), str(dst))
        moved.append(
            {
                "file_type": entry["file_type"],
                "file_name": entry["new_name"],
                "dest_path": str(dst),
            }
        )

    return moved