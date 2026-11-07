"""Unit tests for the shared loudness gain calculation.

These tests pin the gain formula so the ``target_offset`` regression
(storing loudnorm's near-zero residual instead of the real gain) cannot
return unnoticed.
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

from src.db.sync.loudness import (
    LOUDNESS_TARGET,
    TRUE_PEAK_CEILING,
    analyze_loudness,
    compute_gain_db,
)


class TestComputeGainDb:
    def test_quiet_track_gets_positive_gain(self) -> None:
        # A quiet track at -24 LUFS with a low peak should be boosted.
        gain = compute_gain_db(input_i=-24.0, input_tp=-10.0)
        assert gain == LOUDNESS_TARGET - (-24.0)  # +8 dB

    def test_loud_track_gets_negative_gain(self) -> None:
        gain = compute_gain_db(input_i=-10.0, input_tp=-1.0)
        assert gain == LOUDNESS_TARGET - (-10.0)  # -6 dB

    def test_on_target_track_gets_near_zero_gain(self) -> None:
        gain = compute_gain_db(input_i=-16.0, input_tp=-7.0)
        assert gain == 0.0

    def test_gain_clamped_to_true_peak_ceiling(self) -> None:
        # Quiet track but a hot peak: full +8 dB would push the peak to
        # -0.5 dBTP (above the -1 ceiling), so it must clamp to +7 dB.
        gain = compute_gain_db(input_i=-24.0, input_tp=-8.0)
        assert gain == TRUE_PEAK_CEILING - (-8.0)  # +7 dB, not +8

    def test_clamp_prevents_clipping(self) -> None:
        input_tp = -3.0
        gain = compute_gain_db(input_i=-30.0, input_tp=input_tp)
        assert input_tp + gain <= TRUE_PEAK_CEILING


def _ffmpeg_result(payload: dict) -> MagicMock:
    result = MagicMock(spec=subprocess.CompletedProcess)
    result.stderr = "log prefix " + json.dumps(payload) + " log suffix"
    return result


class TestAnalyzeLoudness:
    def test_parses_gain_from_measured_input_i(self) -> None:
        payload = {
            "input_i": "-16.84",
            "input_tp": "-7.12",
            "target_offset": "-0.89",  # must be ignored
        }
        with patch(
            "src.db.sync.loudness.subprocess.run",
            return_value=_ffmpeg_result(payload),
        ):
            gain = analyze_loudness("/fake/song.mp3")
        # -16 - (-16.84) = +0.84, NOT the -0.89 target_offset.
        assert gain is not None
        assert abs(gain - 0.84) < 1e-6

    def test_returns_none_on_missing_json(self) -> None:
        result = MagicMock(spec=subprocess.CompletedProcess)
        result.stderr = "no json here"
        with patch("src.db.sync.loudness.subprocess.run", return_value=result):
            assert analyze_loudness("/fake/song.mp3") is None

    def test_returns_none_on_timeout(self) -> None:
        with patch(
            "src.db.sync.loudness.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=300),
        ):
            assert analyze_loudness("/fake/song.mp3") is None
