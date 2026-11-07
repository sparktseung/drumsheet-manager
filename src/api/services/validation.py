from __future__ import annotations

import re
from pathlib import Path
import polars as pl

# ── Patterns that Excel / LibreOffice may auto-convert ──────────────

BOOLEAN_LIKE = frozenset({"true", "false", "t", "f", "yes", "no", "on", "off"})

EXCEL_ERROR_VALUES = frozenset(
    {
        "#n/a",
        "#value!",
        "#ref!",
        "#div/0!",
        "#num!",
        "#name?",
        "#null!",
        "#calc!",
        "#spill!",
        "#field!",
    }
)

# Matches pure numeric strings: 123, -1.5, .5, 1e5, +42, etc.
_NUMERIC_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")

# Matches date-like strings: 1/2, 01/02, 1-2, 2024/01/01, etc.
_DATE_RE = re.compile(r"^\d{1,4}[/\-.]\d{1,2}([/\-.]\d{1,4})?$")

# Matches month-name-like strings: Jan, January, etc.
_MONTH_NAMES_RE = re.compile(
    r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    r"(uary|ruary|ch|ril|e|y|ust|tember|ober|ember)?$",
    re.IGNORECASE,
)

# Characters that trigger formula evaluation in Excel / LibreOffice.
_FORMULA_TRIGGERS = frozenset({"=", "+", "-", "@"})

# Control characters rejected by PostgreSQL (except tab, lf, cr).
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

# Max VARCHAR length in the song_master table.
MAX_VARCHAR_LENGTH = 255

# Characters forbidden in file names across macOS / Windows / Linux.
_FORBIDDEN_FILENAME_CHARS_RE = re.compile(r"[/\\:*?\"<>|]")


def validate_name(value: str, field_label: str) -> list[str]:
    """Validate a song name field for all known edge cases.

    Returns a list of human-readable error messages (empty = valid).
    """
    errors: list[str] = []

    # ── Emptiness ──
    if not value:
        errors.append(f"{field_label} is empty")
        return errors

    stripped = value.strip()
    if not stripped:
        errors.append(f"{field_label} is whitespace-only")
        return errors

    # ── Whitespace ──
    if stripped != value:
        errors.append(f"{field_label} has leading or trailing whitespace")

    # ── Length ──
    if len(stripped) > MAX_VARCHAR_LENGTH:
        errors.append(
            f"{field_label} is {len(stripped)} characters"
            f" (max {MAX_VARCHAR_LENGTH})"
        )

    lower = stripped.lower()

    # ── Boolean-like ──
    if lower in BOOLEAN_LIKE:
        errors.append(
            f"{field_label} '{stripped}' is a boolean-like value"
            " and would be auto-converted by Excel"
        )

    # ── Excel error values ──
    if lower in EXCEL_ERROR_VALUES:
        errors.append(f"{field_label} '{stripped}' is an Excel error value")

    # ── Pure numeric ──
    if _NUMERIC_RE.match(stripped):
        errors.append(
            f"{field_label} '{stripped}' is purely numeric and"
            " would be auto-converted to a number by Excel"
        )

    # ── Date-like ──
    if _DATE_RE.match(stripped):
        errors.append(
            f"{field_label} '{stripped}' looks like a date and"
            " may be auto-converted by Excel"
        )

    # ── Month-name-like ──
    if _MONTH_NAMES_RE.match(stripped):
        errors.append(
            f"{field_label} '{stripped}' looks like a month name"
            " and may be auto-converted to a date by Excel"
        )

    # ── Formula triggers ──
    if stripped and stripped[0] in _FORMULA_TRIGGERS:
        errors.append(
            f"{field_label} starts with '{stripped[0]}' which"
            " may trigger formula evaluation in Excel"
        )

    # ── NUL bytes (rejected by PostgreSQL) ──
    if "\x00" in stripped:
        errors.append(f"{field_label} contains NUL bytes")

    # ── Other control characters ──
    ctrl_match = _CONTROL_CHARS_RE.search(stripped)
    if ctrl_match:
        errors.append(
            f"{field_label} contains control character"
            f" U+{ord(ctrl_match.group()):04X}"
        )

    return errors


def validate_filename(name: str, field_label: str) -> list[str]:
    """Validate a file name component for filesystem safety."""
    errors: list[str] = []

    if not name or not name.strip():
        errors.append(f"{field_label} is empty")
        return errors

    forbidden = _FORBIDDEN_FILENAME_CHARS_RE.search(name)
    if forbidden:
        errors.append(
            f"{field_label} contains forbidden character"
            f" '{forbidden.group()}'"
        )

    if name in (".", ".."):
        errors.append(f"{field_label} is a reserved name '{name}'")

    return errors


def validate_file_in_dir(
    file_path: str,
    allowed_dir: str,
    field_label: str,
) -> list[str]:
    """Validate that a file exists and resides within *allowed_dir*."""
    errors: list[str] = []

    if not file_path:
        return errors  # optional field

    p = Path(file_path)
    allowed = Path(allowed_dir).resolve()

    if not p.exists():
        errors.append(f"{field_label}: file not found: {file_path}")
        return errors

    try:
        resolved = p.resolve()
    except (OSError, RuntimeError):
        errors.append(f"{field_label}: cannot resolve path: {file_path}")
        return errors

    try:
        resolved.relative_to(allowed)
    except ValueError:
        errors.append(f"{field_label}: file is outside the allowed directory")

    return errors


def validate_no_duplicate_in_master(
    *,
    master_file: str,
    artist_en: str,
    song_name_en: str,
) -> list[str]:
    """Check that the song does not already exist in the master list."""

    errors: list[str] = []
    master_path = Path(master_file)

    if not master_path.exists():
        return errors  # handled elsewhere

    try:
        df = pl.read_excel(master_path)
    except Exception:
        return errors  # handled elsewhere

    if "artist_en" not in df.columns or "song_name_en" not in df.columns:
        return errors

    existing = df.filter(
        (pl.col("artist_en").str.strip_chars() == artist_en)
        & (pl.col("song_name_en").str.strip_chars() == song_name_en)
    )
    if not existing.is_empty():
        errors.append(
            f"'{artist_en} - {song_name_en}' already exists"
            " in the master list"
        )

    return errors


def _normalized_stem(
    artist_en: str,
    song_name_en: str,
    artist_local: str | None = None,
    song_name_local: str | None = None,
) -> str:
    """Return the normalized file stem used by the discovery pipeline."""
    if artist_local and song_name_local:
        return (
            f"{artist_local} - {song_name_local}"
            f" - {artist_en} - {song_name_en}"
        )
    return f"{artist_en} - {song_name_en}"


def _case_insensitive_exists(path: Path) -> bool:
    """Check if a file exists, accounting for case-insensitive collisions.

    On case-insensitive filesystems (macOS, Windows) ``Path.exists()``
    already handles this.  On case-sensitive filesystems (Linux) we
    explicitly check the parent directory for a name that differs only
    by case.
    """
    if path.exists():
        return True
    parent = path.parent
    if not parent.is_dir():
        return False
    try:
        entries = {p.name for p in parent.iterdir()}
    except PermissionError:
        return False
    return path.name.lower() in {n.lower() for n in entries}


def validate_normalized_filenames(
    *,
    artist_en: str,
    song_name_en: str,
    artist_local: str | None = None,
    song_name_local: str | None = None,
    extensions: list[str],
    staging_folder: str,
    data_folder: str,
) -> list[str]:
    """Check that normalized file names won't conflict in staging or data.

    Uses the same stem logic as the actual rename step so the check
    matches what will happen at insertion time.
    """
    errors: list[str] = []
    stem = _normalized_stem(
        artist_en=artist_en,
        song_name_en=song_name_en,
        artist_local=artist_local,
        song_name_local=song_name_local,
    )

    for folder_label, folder in [
        ("staging", staging_folder),
        ("data", data_folder),
    ]:
        root = Path(folder)
        if not root.is_dir():
            continue
        for ext in extensions:
            target = root / f"{stem}{ext}"
            if _case_insensitive_exists(target):
                errors.append(
                    f"'{target.name}' already exists in the"
                    f" {folder_label} folder"
                )

    return errors
