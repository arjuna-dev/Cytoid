#!/usr/bin/env python3
"""Build Luna's sparse easy-chart candidate from the measured beat grid."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
CANDIDATE_DIR = Path(__file__).resolve().parent
ANALYSIS_PATH = ROOT / "docs/audio/hladini_shakti_excerpt.analysis.json"
TIME_BASE = 480


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_chart(analysis: dict[str, Any]) -> dict[str, Any]:
    beats = analysis["beats"]
    first_beat = float(analysis["analysis"]["first_beat_seconds"])

    # A two-beat pulse is intentionally forgiving for an easy chart. The
    # measured tempo list remains beat-accurate so expressive timing is kept.
    selected_beats = list(range(0, len(beats), 2))
    page_list = [
        {
            "start_tick": page_index * 2 * TIME_BASE,
            "end_tick": (page_index + 1) * 2 * TIME_BASE,
            "scan_line_direction": 1 if page_index % 2 == 0 else -1,
        }
        for page_index in range(len(selected_beats))
    ]

    x_pattern = (0.50, 0.38, 0.62, 0.50, 0.30, 0.70, 0.50, 0.50)
    note_list = []
    for note_id, beat_index in enumerate(selected_beats):
        note_list.append(
            {
                "page_index": note_id,
                "type": 0,
                "id": note_id,
                "tick": beat_index * TIME_BASE,
                "x": x_pattern[note_id % len(x_pattern)],
                "has_sibling": False,
                "hold_tick": 0,
                "next_id": 0,
                "is_forward": False,
                "approach_rate": 1.0,
            }
        )

    intervals = [
        float(beats[index + 1]["time_seconds"]) - float(beats[index]["time_seconds"])
        for index in range(len(beats) - 1)
    ]
    values = [max(450000, min(800000, int(round(interval * 1_000_000)))) for interval in intervals]
    values.append(values[-1])

    return {
        "format_version": 0,
        "time_base": TIME_BASE,
        "music_offset": round(-first_beat, 6),
        "display_background": False,
        "page_list": page_list,
        "tempo_list": [
            {"tick": index * TIME_BASE, "value": value}
            for index, value in enumerate(values)
        ],
        "event_order_list": [],
        "note_list": note_list,
    }


def build_level() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "version": 1,
        "id": "kiirtaniyas.hladini_excerpt_luna_easy",
        "title": "Hladini Shakti Kiirtana - Excerpt (Luna Easy Candidate)",
        "artist": "Bhuvanesh",
        "charter": "Luna candidate, generated from measured timing",
        "music": {"path": "music.mp3"},
        "music_preview": {"path": "music.mp3"},
        "charts": [
            {
                "type": "easy",
                "difficulty": 3,
                "path": "chart.easy.json",
            }
        ],
    }


def main() -> int:
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    analysis = json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))
    write_json(CANDIDATE_DIR / "chart.easy.json", build_chart(analysis))
    write_json(CANDIDATE_DIR / "level.json", build_level())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
