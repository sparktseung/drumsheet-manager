from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.sql.elements import ColumnElement

DEFAULT_SCHEMA = "drumsheets"
DEFAULT_TABLE = "songs"
UID_NAMESPACE = uuid.UUID("1e088bc4-e188-4705-b6ef-411f67147076")
EXPECTED_GENRES = ("CPOP", "JPOP", "KPOP")


@dataclass(frozen=True)
class FilterSpec:
    """Filter descriptor for query builder helpers.

    Example:
        FilterSpec("difficulty", "eq", "intermediate")
    """

    column: str
    op: str
    value: Any


class DrumsheetPostgresDB:
    """Small SQLAlchemy Core wrapper for managing drumsheet data in Postgres.

    This class intentionally separates:
    - Implemented database behavior (schema/table management, CRUD helpers).
    - Scaffolding hooks for local filesystem discovery/sync to be filled in
      later.
    """

    def __init__(
        self,
        dsn: str,
        schema: str = DEFAULT_SCHEMA,
        table_name: str = DEFAULT_TABLE,
    ) -> None:
        self.schema = schema
        self.table_name = table_name
        self.engine: Engine = sa.create_engine(dsn, future=True)
        self.metadata = sa.MetaData(schema=schema)
        self._reflected_table: sa.Table | None = None

    def ensure_schema(self) -> None:
        """Create the target schema when it does not exist."""
        quoted_schema = self.schema.replace('"', '""')
        statement = sa.text(f'CREATE SCHEMA IF NOT EXISTS "{quoted_schema}"')
        with self.engine.begin() as conn:
            conn.execute(statement)

    def create_table(self, *, drop_existing: bool = False) -> str:
        """Create the canonical drumsheet table in the configured schema."""
        self.ensure_schema()
        table = self._build_table()

        with self.engine.begin() as conn:
            if drop_existing:
                table.drop(conn, checkfirst=True)
            table.create(conn, checkfirst=True)

        return self.table_name

    def ensure_table(self) -> str:
        """Idempotently create schema + canonical table."""
        return self.create_table(drop_existing=False)

    def insert_rows(self, rows: list[dict[str, Any]]) -> int:
        """Insert rows into the canonical table and return affected count."""
        if not rows:
            return 0

        rows = self._with_computed_uid(rows)
        table = self.get_table()
        stmt = (
            pg_insert(table)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["uid"])
        )
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return int(result.rowcount or 0)

    def upsert_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        conflict_column: str = "uid",
    ) -> int:
        """Upsert rows using a single conflict target column."""
        if not rows:
            return 0

        rows = self._with_computed_uid(rows)
        table = self.get_table()
        stmt = pg_insert(table).values(rows)

        update_map = {
            col.name: stmt.excluded[col.name]
            for col in table.columns
            if col.name not in {"id", conflict_column, "created_ts"}
        }
        update_map["modified_ts"] = sa.func.now()

        stmt = stmt.on_conflict_do_update(
            index_elements=[table.c[conflict_column]],
            set_=update_map,
            where=(
                stmt.excluded.file_last_modified > table.c.file_last_modified
            ),
        )

        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return int(result.rowcount or 0)

    def select_rows(
        self,
        *,
        columns: list[str] | None = None,
        filters: list[FilterSpec] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Select rows from a table with optional filters, sort, and limit."""
        table = self.get_table()

        selected = [table.c[name] for name in columns] if columns else [table]
        stmt = sa.select(*selected)

        for condition in self._build_conditions(table, filters or []):
            stmt = stmt.where(condition)

        if order_by:
            direction = sa.asc
            col_name = order_by
            if order_by.startswith("-"):
                direction = sa.desc
                col_name = order_by[1:]
            stmt = stmt.order_by(direction(table.c[col_name]))

        if limit is not None:
            stmt = stmt.limit(limit)

        with self.engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]

    def update_rows(
        self,
        values: dict[str, Any],
        *,
        filters: list[FilterSpec] | None = None,
    ) -> int:
        """Update matching rows and return affected count."""
        table = self.get_table()
        update_values = {"modified_ts": sa.func.now(), **values}
        stmt = sa.update(table).values(**update_values)

        for condition in self._build_conditions(table, filters or []):
            stmt = stmt.where(condition)

        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return int(result.rowcount or 0)

    def delete_rows(
        self,
        *,
        filters: list[FilterSpec] | None = None,
    ) -> int:
        """Delete matching rows and return affected count."""
        table = self.get_table()
        stmt = sa.delete(table)

        for condition in self._build_conditions(table, filters or []):
            stmt = stmt.where(condition)

        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return int(result.rowcount or 0)

    def get_table(self) -> sa.Table:
        """Reflect and return a table object from the configured schema."""
        if self._reflected_table is None:
            self._reflected_table = sa.Table(
                self.table_name,
                sa.MetaData(),
                schema=self.schema,
                autoload_with=self.engine,
            )
        return self._reflected_table

    def discover_genres_from_local(self, root_path: Path) -> list[str]:
        """Scaffold: inspect local folders and return inferred genre names."""
        root = Path(root_path).expanduser().resolve()
        discovered: list[str] = []

        for genre in EXPECTED_GENRES:
            if (root / genre).is_dir():
                discovered.append(genre)

        return discovered

    def build_rows_from_local(
        self,
        genre_folder: Path,
    ) -> list[dict[str, Any]]:
        """Scaffold: parse a local genre folder into row dictionaries."""
        folder = Path(genre_folder).expanduser().resolve()
        if not folder.is_dir():
            return []

        genre = folder.name.upper()
        rows: list[dict[str, Any]] = []

        for pdf_path in sorted(folder.glob("*.pdf")):
            parsed = self._parse_filename_parts(pdf_path.stem)
            file_stat = pdf_path.stat()
            rows.append(
                {
                    "genre": genre,
                    "artist_local": parsed["artist_local"],
                    "song_name_local": parsed["song_name_local"],
                    "artist_en": parsed["artist_en"],
                    "song_name_en": parsed["song_name_en"],
                    "file_path": str(folder),
                    "file_name": pdf_path.name,
                    "full_path": str(pdf_path),
                    "file_last_modified": datetime.fromtimestamp(
                        file_stat.st_mtime, tz=timezone.utc
                    ),
                }
            )

        return rows

    def sync_local_to_db(self, root_path: Path) -> dict[str, int]:
        """Scaffold: scan local content and sync records into the database."""
        self.ensure_table()

        root = Path(root_path).expanduser().resolve()
        genres = self.discover_genres_from_local(root)

        all_rows: list[dict[str, Any]] = []
        for genre in genres:
            all_rows.extend(self.build_rows_from_local(root / genre))

        upserted_rows = self.upsert_rows(all_rows) if all_rows else 0

        return {
            "genres_found": len(genres),
            "scanned_files": len(all_rows),
            "upserted_rows": upserted_rows,
        }

    def _parse_filename_parts(self, file_stem: str) -> dict[str, str]:
        """Parse filename into metadata fields with lenient fallback support.

        Expected canonical shape:
            artist_local - song_name_local - artist_en - song_name_en

        Some segments may be missing; this parser normalizes and pads values.
        Excess segments beyond index 3 are joined back into song_name_en.
        """
        parts = [
            self._normalize_name_component(part)
            for part in file_stem.split(" - ")
        ]
        parts = [part for part in parts if part]

        artist_local = parts[0] if len(parts) > 0 else "unknown"
        song_name_local = parts[1] if len(parts) > 1 else file_stem.strip()
        artist_en = parts[2] if len(parts) > 2 else artist_local
        song_name_en = (
            " - ".join(parts[3:]) if len(parts) > 3 else song_name_local
        )

        return {
            "artist_local": artist_local,
            "song_name_local": song_name_local,
            "artist_en": artist_en,
            "song_name_en": song_name_en,
        }

    def _normalize_name_component(self, value: str) -> str:
        """Normalize filename segment while keeping meaning readable."""
        return " ".join(value.replace("_", " ").split()).strip()

    def _build_table(self) -> sa.Table:
        return sa.Table(
            self.table_name,
            self.metadata,
            sa.Column(
                "id",
                sa.BigInteger,
                primary_key=True,
                autoincrement=True,
            ),
            sa.Column("uid", sa.Uuid, nullable=False, unique=True),
            sa.Column("genre", sa.String(128), nullable=False),
            sa.Column("artist_local", sa.String(255), nullable=False),
            sa.Column("song_name_local", sa.String(255), nullable=False),
            sa.Column("artist_en", sa.String(255), nullable=False),
            sa.Column("song_name_en", sa.String(255), nullable=False),
            sa.Column("file_path", sa.Text, nullable=False),
            sa.Column("file_name", sa.Text, nullable=False),
            sa.Column("full_path", sa.Text, nullable=False, unique=True),
            sa.Column(
                "file_last_modified",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.Column(
                "created_ts",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "modified_ts",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
            sa.Index(
                f"ix_{self.table_name}_genre",
                "genre",
            ),
            schema=self.schema,
        )

    def _build_conditions(
        self,
        table: sa.Table,
        filters: list[FilterSpec],
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        for filt in filters:
            col = table.c[filt.column]
            op = filt.op.lower()
            value = filt.value

            if op == "eq":
                conditions.append(col == value)
            elif op == "ne":
                conditions.append(col != value)
            elif op == "gt":
                conditions.append(col > value)
            elif op == "gte":
                conditions.append(col >= value)
            elif op == "lt":
                conditions.append(col < value)
            elif op == "lte":
                conditions.append(col <= value)
            elif op == "in":
                conditions.append(col.in_(value))
            elif op == "like":
                conditions.append(col.like(value))
            elif op == "ilike":
                conditions.append(col.ilike(value))
            else:
                raise ValueError(f"Unsupported filter operation: {filt.op}")

        return conditions

    def _with_computed_uid(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for row in rows:
            candidate = dict(row)
            if "uid" not in candidate or candidate["uid"] in (None, ""):
                candidate["uid"] = self._compute_uid(candidate)
            enriched.append(candidate)
        return enriched

    def _compute_uid(self, row: dict[str, Any]) -> uuid.UUID:
        parts = [
            self._required_uid_part(row, "genre"),
            self._required_uid_part(row, "artist_local"),
            self._required_uid_part(row, "song_name_local"),
        ]
        return uuid.uuid5(UID_NAMESPACE, "|".join(parts))

    def _required_uid_part(self, row: dict[str, Any], key: str) -> str:
        raw_value = row.get(key)
        if raw_value is None:
            raise ValueError(f"Missing required uid source field: {key}")

        value = self._normalize_uid_part(str(raw_value))
        if not value:
            raise ValueError(f"Empty required uid source field: {key}")

        return value

    def _normalize_uid_part(self, value: str) -> str:
        """Normalize uid input by collapsing whitespace and lowercasing."""
        return " ".join(value.split()).lower()
