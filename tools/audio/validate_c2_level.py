#!/usr/bin/env python3
"""Validate a local level metadata file and its C2 chart timing."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


ALLOWED_NOTE_TYPES = {0, 1, 3, 4}
ID_PATTERN = re.compile(r"^[a-z0-9_]+([-_.][a-z0-9_]+)*$")


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def chart_time(tick: int, tempo_list: list[dict[str, Any]], time_base: int) -> float:
    """Mirror Chart.ConvertToTime for the fields used by this validator."""

    result = 0.0
    current_tick = 0
    zone = 0
    for index in range(1, len(tempo_list)):
        if tempo_list[index]["tick"] >= tick:
            break
        result += (
            (tempo_list[index]["tick"] - current_tick)
            * 1e-6
            * tempo_list[index - 1]["value"]
            / time_base
        )
        current_tick = tempo_list[index]["tick"]
        zone = index
    result += (tick - current_tick) * 1e-6 * tempo_list[zone]["value"] / time_base
    return result


def validate(level_path: Path, analysis_path: Path | None, chart_type: str = "easy") -> dict[str, Any]:
    require(level_path.is_file(), f"missing level metadata: {level_path}")
    level = json.loads(level_path.read_text(encoding="utf-8"))
    require(ID_PATTERN.fullmatch(level.get("id", "")) is not None, "invalid level id")
    charts = level.get("charts")
    require(isinstance(charts, list) and charts, "level has no charts")
    selected = next((item for item in charts if item.get("type") == chart_type), None)
    require(selected is not None, f"level has no {chart_type} chart")
    chart_path = level_path.parent / selected["path"]
    require(chart_path.is_file(), f"missing chart: {chart_path}")
    chart = json.loads(chart_path.read_text(encoding="utf-8"))

    time_base = int(chart.get("time_base", 0))
    require(time_base > 0, "time_base must be positive")
    pages = chart.get("page_list")
    tempos = chart.get("tempo_list")
    notes = chart.get("note_list")
    require(isinstance(pages, list) and pages, "chart has no pages")
    require(isinstance(tempos, list) and tempos, "chart has no tempo entries")
    require(isinstance(notes, list) and notes, "chart has no notes")
    require(all(isinstance(item.get("tick"), (int, float)) for item in tempos), "tempo tick is not numeric")
    require(all(isinstance(item.get("value"), (int, float)) for item in tempos), "tempo value is not numeric")
    require(all(item["value"] > 0 for item in tempos), "tempo value must be positive")
    require(all(a["tick"] < b["tick"] for a, b in zip(tempos, tempos[1:])), "tempo ticks are not strictly increasing")
    require(all(page["end_tick"] > page["start_tick"] for page in pages), "page span must be positive")
    require(all(a["end_tick"] <= b["start_tick"] for a, b in zip(pages, pages[1:])), "pages overlap or are out of order")

    note_ids = []
    note_times = []
    for note in notes:
        require(note.get("type") in ALLOWED_NOTE_TYPES, f"unsupported note type: {note.get('type')}")
        require(0 <= note.get("page_index", -1) < len(pages), "note page index is outside page list")
        require(0.0 <= float(note.get("x", -1.0)) <= 1.0, "note x must be in [0, 1]")
        note_ids.append(note.get("id"))
        note_times.append(chart_time(int(note["tick"]), tempos, time_base))
    require(len(set(note_ids)) == len(note_ids), "note ids are not unique")
    require(all(a <= b for a, b in zip(note_times, note_times[1:])), "note times are not chronological")
    require(all(math.isfinite(value) for value in note_times), "note time is not finite")

    report: dict[str, Any] = {
        "level": str(level_path),
        "chart": str(chart_path),
        "level_id": level["id"],
        "note_count": len(notes),
        "page_count": len(pages),
        "tempo_count": len(tempos),
        "music_offset": float(chart.get("music_offset", 0.0)),
        "chart_duration_seconds": round(note_times[-1], 6),
    }
    if analysis_path is not None:
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        beats = analysis.get("beats", [])
        first_beat = float(analysis["analysis"]["first_beat_seconds"])
        if len(beats) == len(notes):
            expected_times = [float(beat["time_seconds"]) - first_beat for beat in beats]
            comparison_mode = "one_note_per_measured_beat"
        else:
            # Sparse easy charts may intentionally select a measured subset.
            # Only accept exact beat ticks in this mode so a chart cannot pass
            # by merely being close to an onset.
            selected_indices = []
            for note in notes:
                tick = int(note["tick"])
                beat_index, remainder = divmod(tick, time_base)
                require(remainder == 0, "sparse analysis validation requires notes on measured beat ticks")
                require(0 <= beat_index < len(beats), "sparse analysis note points outside measured beats")
                selected_indices.append(beat_index)
            require(len(set(selected_indices)) == len(selected_indices), "sparse analysis notes reuse a measured beat")
            expected_times = [float(beats[index]["time_seconds"]) - first_beat for index in selected_indices]
            report_indices = selected_indices
            comparison_mode = "sparse_measured_beat_subset"

        errors = [note_time - expected for note_time, expected in zip(note_times, expected_times)]
        max_error = max(abs(value) for value in errors) if errors else 0.0
        require(max_error <= 0.005, f"chart timing differs from analysis by {max_error:.6f}s")
        require(abs(float(chart.get("music_offset", 0.0)) + first_beat) <= 0.005, "music_offset does not align first beat")
        report["analysis"] = str(analysis_path)
        report["analysis_comparison_mode"] = comparison_mode
        report["max_chart_analysis_error_seconds"] = round(max_error, 6)
        if len(beats) != len(notes):
            report["selected_measured_beat_indices"] = report_indices
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", type=Path, required=True)
    parser.add_argument("--analysis", type=Path)
    parser.add_argument("--chart-type", default="easy", help="chart type to validate (default: easy)")
    args = parser.parse_args()
    report = validate(args.level, args.analysis, args.chart_type)
    print(json.dumps({"status": "ok", **report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
