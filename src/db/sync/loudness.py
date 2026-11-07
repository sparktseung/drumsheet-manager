"""Shared loudness analysis for song audio.

Single source of truth for the playback-gain calculation used by both the
sync runner and the backfill script. Keeping it here prevents the two
callers from drifting apart (which previously let a wrong formula persist
in one of them).
"""

from __future__ import annotations

import json
import subprocess

LOUDNESS_TARGET = -16  # Target integrated loudness in LUFS
TRUE_PEAK_CEILING = -1.0  # Max true peak (dBTP) after gain, to avoid clipping

# Bump this whenever the gain algorithm changes. The sync runner keys its
# cached gain on this version so stale values are recomputed automatically
# instead of silently persisting.
LOUDNESS_ALGO_VERSION = 2


def compute_gain_db(input_i: float, input_tp: float) -> float:
    """Return the playback gain (dB) for a measured track.

    ``input_i`` is the measured integrated loudness (LUFS) and ``input_tp``
    the measured true peak (dBTP). The gain brings the track to
    LOUDNESS_TARGET, clamped so the true peak never exceeds
    TRUE_PEAK_CEILING (prevents clipping on quiet, high-peak tracks).
    """
    gain = LOUDNESS_TARGET - input_i
    max_gain = TRUE_PEAK_CEILING - input_tp
    return min(gain, max_gain)


def analyze_loudness(file_path: str) -> float | None:
    """Run FFmpeg loudnorm analysis and return the playback gain (dB).

    Returns None if analysis fails.

    The gain is derived from the measured integrated loudness (``input_i``)
    via :func:`compute_gain_db`, not loudnorm's ``target_offset`` — the
    latter is only the small linear/dynamic residual and is near zero for
    most files, which left quiet songs essentially unnormalized.
    """
    cmd = [
        "ffmpeg",
        "-i",
        file_path,
        "-af",
        f"loudnorm=I={LOUDNESS_TARGET}:print_format=json",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        stderr = result.stderr
        json_start = stderr.find("{")
        json_end = stderr.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(stderr[json_start:json_end])
            input_i = float(data["input_i"])
            input_tp = float(data["input_tp"])
            return compute_gain_db(input_i, input_tp)
    except (
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
        ValueError,
        OSError,
    ):
        pass
    return None


__all__ = [
    "LOUDNESS_TARGET",
    "TRUE_PEAK_CEILING",
    "LOUDNESS_ALGO_VERSION",
    "compute_gain_db",
    "analyze_loudness",
]
