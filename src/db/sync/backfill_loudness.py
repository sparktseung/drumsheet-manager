"""One-off script: populate loudness_gain_db for existing rows that have NULL.

Usage:
    python -m src.db.sync.backfill_loudness

Requires POSTGRES_DB_DSN and POSTGRES_DB_SCHEMA in .env (same as the app).
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys

import sqlalchemy as sa
from sqlalchemy.engine import Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger("backfill_loudness")

LOUDNESS_TARGET = -16


def _analyze_loudness(file_path: str) -> float | None:
    cmd = [
        "ffmpeg",
        "-i", file_path,
        "-af", f"loudnorm=I={LOUDNESS_TARGET}:print_format=json",
        "-f", "null",
        "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        stderr = result.stderr
        json_start = stderr.find("{")
        json_end = stderr.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(stderr[json_start:json_end])
            return float(data["target_offset"])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def backfill(engine: Engine, schema: str) -> int:
    stmt = sa.text(
        f"SELECT song_id, file_path"
        f" FROM {schema}.song_audio"
        f" WHERE loudness_gain_db IS NULL"
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

    if not rows:
        logger.info("No rows with NULL loudness_gain_db found.")
        return 0

    total = len(rows)
    updated = 0
    for i, row in enumerate(rows, 1):
        song_id = row["song_id"]
        file_path = row["file_path"]
        logger.info("[%d/%d] Analyzing %s ...", i, total, file_path)
        gain = _analyze_loudness(file_path)
        if gain is None:
            logger.warning("  Analysis failed for %s", file_path)
            continue

        upd = sa.text(
            f"UPDATE {schema}.song_audio"
            f" SET loudness_gain_db = :gain, updated_at = NOW()"
            f" WHERE song_id = :song_id"
        )
        with engine.begin() as conn:
            conn.execute(upd, {"gain": gain, "song_id": song_id})
        logger.info("  -> gain = %.1f dB", gain)
        updated += 1

    return updated


def main() -> None:
    from src.api.config import get_settings

    settings = get_settings()
    engine = sa.create_engine(settings.dsn, future=True)
    try:
        n = backfill(engine, settings.schema)
        logger.info("Done. Updated %d row(s).", n)
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
