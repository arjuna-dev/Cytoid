#!/usr/bin/env python3
"""Validate the Luna easy candidate against the measured beat grid."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


CANDIDATE_DIR = Path(__file__).resolve().parent
ROOT = CANDIDATE_DIR.parents[3]
ANALYSIS_PATH = ROOT / "docs/audio/hladini_shakti_excerpt.analysis.json"
TOOLS_PATH = ROOT / "tools/audio"
sys.path.insert(0, str(TOOLS_PATH))

from validate_c2_level import chart_time, validate  # noqa: E402


TIME_BASE = 480


def main() -> int:
    level_path = CANDIDATE_DIR / "level.json"
    chart_path = CANDIDATE_DIR / "chart.easy.json"
    analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    base_report = validate(level_path, None)

    beats = analysis["beats"]
    tempos = chart["tempo_list"]
    notes = chart["note_list"]
    first_beat = float(analysis["analysis"]["first_beat_seconds"])
    expected_indices = list(range(0, len(beats), 2))
    actual_indices = [int(note["tick"]) // TIME_BASE for note in notes]
    require_equal = actual_indices == expected_indices
    if not require_equal:
        raise SystemExit("FAIL: candidate does not select every second measured beat")

    errors = [
        chart_time(int(note["tick"]), tempos, TIME_BASE)
        - (float(beats[beat_index]["time_seconds"]) - first_beat)
        for note, beat_index in zip(notes, expected_indices)
    ]
    note_times = [float(beats[index]["time_seconds"]) for index in expected_indices]
    gaps = [right - left for left, right in zip(note_times, note_times[1:])]
    type_counts = Counter(int(note["type"]) for note in notes)
    hold_count = sum(1 for note in notes if int(note.get("hold_tick", 0)) > 0)
    sibling_count = sum(1 for note in notes if bool(note.get("has_sibling", False)))

    report = {
        "status": "ok",
        "candidate": "luna_easy",
        "level": str(level_path.relative_to(ROOT)),
        "chart": str(chart_path.relative_to(ROOT)),
        "analysis": str(ANALYSIS_PATH.relative_to(ROOT)),
        "timing_source": "measured beat grid, piecewise tempo map",
        "note_count": len(notes),
        "measured_beat_count": len(beats),
        "density_ratio": round(len(notes) / len(beats), 6),
        "selection_rule": "every second measured beat, starting at beat 0",
        "first_selected_beat_index": expected_indices[0],
        "last_selected_beat_index": expected_indices[-1],
        "max_chart_analysis_error_seconds": round(max(abs(error) for error in errors), 6),
        "note_gap_seconds": {
            "minimum": round(min(gaps), 6),
            "maximum": round(max(gaps), 6),
            "mean": round(sum(gaps) / len(gaps), 6),
        },
        "note_type_counts": {str(key): value for key, value in sorted(type_counts.items())},
        "hold_count": hold_count,
        "sibling_count": sibling_count,
        "page_count": len(chart["page_list"]),
        "tempo_count": len(tempos),
        "music_offset": chart["music_offset"],
        "base_validator": base_report,
    }
    (CANDIDATE_DIR / "validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
