"""One-off script: populate loudness_gain_db for existing rows.

Usage:
    python -m src.db.sync.backfill_loudness         # only NULL gains
    python -m src.db.sync.backfill_loudness --all   # recompute every row

Requires POSTGRES_DB_DSN and POSTGRES_DB_SCHEMA in .env (same as the app).
"""

from __future__ import annotations

import logging
import sys

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from src.db.sync.loudness import LOUDNESS_ALGO_VERSION, analyze_loudness

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger("backfill_loudness")


def backfill(engine: Engine, schema: str, recompute_all: bool = False) -> int:
    stale = f" WHERE loudness_algo_version IS DISTINCT FROM {LOUDNESS_ALGO_VERSION}"
    where = "" if recompute_all else stale
    stmt = sa.text(
        f"SELECT song_id, file_path" f" FROM {schema}.song_audio" f"{where}"
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

    if not rows:
        logger.info("No rows to update found.")
        return 0

    total = len(rows)
    updated = 0
    for i, row in enumerate(rows, 1):
        song_id = row["song_id"]
        file_path = row["file_path"]
        logger.info("[%d/%d] Analyzing %s ...", i, total, file_path)
        gain = analyze_loudness(file_path)
        if gain is None:
            logger.warning("  Analysis failed for %s", file_path)
            continue

        upd = sa.text(
            f"UPDATE {schema}.song_audio"
            f" SET loudness_gain_db = :gain,"
            f" loudness_algo_version = :ver, updated_at = NOW()"
            f" WHERE song_id = :song_id"
        )
        params = {
            "gain": gain,
            "ver": LOUDNESS_ALGO_VERSION,
            "song_id": song_id,
        }
        with engine.begin() as conn:
            conn.execute(upd, params)
        logger.info("  -> gain = %.1f dB", gain)
        updated += 1

    return updated


def main() -> None:
    from src.api.config import get_settings

    recompute_all = "--all" in sys.argv[1:]
    settings = get_settings()
    engine = sa.create_engine(settings.dsn, future=True)
    try:
        n = backfill(engine, settings.schema, recompute_all=recompute_all)
        logger.info("Done. Updated %d row(s).", n)
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
