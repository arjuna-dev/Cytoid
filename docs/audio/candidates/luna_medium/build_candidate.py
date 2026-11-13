#!/usr/bin/env python3
"""Build Luna's medium C2 chart candidate from the measured beat grid.

This candidate intentionally lives outside the canonical level directory. It
uses the inherited Cytoid ``hard`` chart id for the project's conceptual
medium tier, because the current engine exposes Easy, Hard, and Extreme only.
The chart is generated from measured beat intervals and half-beat subdivisions,
never from a fixed BPM assumption.
"""

from __future__ import annotations

import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TIME_BASE = 480
HALF_BEAT = TIME_BASE // 2
ALLOWED_NOTE_TYPES = {0, 1, 3, 4}
REPO_ROOT = Path(__file__).resolve().parents[4]
ANALYSIS_PATH = REPO_ROOT / "docs/audio/hladini_shakti_excerpt.analysis.json"
AUDIO_PATH = REPO_ROOT / "engines/unity/Assets/Kiirtaniyas/Audio/Hladini_shakti_excerpt.mp3"
OUTPUT_DIR = Path(__file__).resolve().parent
CHART_PATH = OUTPUT_DIR / "chart.medium.json"
LEVEL_PATH = OUTPUT_DIR / "level.json"
PACKAGE_PATH = OUTPUT_DIR / "kiirtaniyas.hladini_excerpt_luna_medium.cytoidlevel"
VALIDATION_PATH = OUTPUT_DIR / "validation.json"
VALIDATION_MARKDOWN_PATH = OUTPUT_DIR / "validation.md"
RATIONALE_PATH = OUTPUT_DIR / "rationale.md"


def load_analysis() -> dict[str, Any]:
    return json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))


def measured_tempo_list(beats: list[dict[str, Any]]) -> list[dict[str, int]]:
    intervals = [
        float(beats[index + 1]["time_seconds"]) - float(beats[index]["time_seconds"])
        for index in range(len(beats) - 1)
    ]
    if not intervals:
        intervals = [0.6]
    values = [max(450000, min(800000, int(round(interval * 1_000_000)))) for interval in intervals]
    values.append(values[-1])
    return [{"tick": index * TIME_BASE, "value": value} for index, value in enumerate(values)]


def make_note(
    *,
    note_id: int,
    page_index: int,
    tick: int,
    x: float,
    note_type: int = 0,
    hold_tick: int = 0,
    next_id: int = 0,
) -> dict[str, Any]:
    return {
        "page_index": page_index,
        "type": note_type,
        "id": note_id,
        "tick": tick,
        "x": round(max(0.08, min(0.92, x)), 3),
        "has_sibling": False,
        "hold_tick": hold_tick,
        "next_id": next_id,
        "is_forward": False,
        "approach_rate": 1.0,
    }


def make_chart(analysis: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    beats = list(analysis["beats"])
    count = len(beats)
    pages = [
        {
            "start_tick": index * TIME_BASE,
            "end_tick": (index + 1) * TIME_BASE,
            "scan_line_direction": 1 if index % 2 == 0 else -1,
        }
        for index in range(count)
    ]

    # The patterns keep movement within a comfortable 8th-note grid. A chain
    # occupies one beat with three connected drag notes, and a hold lasts one
    # beat so it never forces an unrelated overlapping gesture.
    main_x = (0.50, 0.30, 0.70, 0.42, 0.58, 0.25, 0.75, 0.50)
    offbeat_x = (0.38, 0.62, 0.22, 0.78, 0.46, 0.54)
    occupied_ticks: set[int] = set()
    scheduled: list[tuple[int, int, float, int, int, int | None]] = []
    # tuple: tick, type, x, hold_tick, page_index, chain_slot marker

    chain_starts = {index for index in range(8, count - 1, 32)}
    hold_starts = {
        index for index in range(4, count, 16) if index not in chain_starts and index + 1 < count
    }
    chord_beats = {
        index for index in range(12, count, 16) if index not in chain_starts and index not in hold_starts
    }

    # Main beat notes, with selected hold and drag variations.
    for index in range(count):
        beat_tick = index * TIME_BASE
        if index in chain_starts:
            chain_ticks = (beat_tick, beat_tick + HALF_BEAT, beat_tick + TIME_BASE)
            chain_ids = [None, None, None]
            for slot, tick in enumerate(chain_ticks):
                chain_ids[slot] = len(scheduled)
                scheduled.append(
                    (
                        tick,
                        3 if slot == 0 else 4,
                        (0.34, 0.52, 0.70)[slot],
                        0,
                        index,
                        slot,
                    )
                )
                occupied_ticks.add(tick)
            continue

        if index in hold_starts:
            scheduled.append((beat_tick, 1, main_x[index % len(main_x)], TIME_BASE, index, None))
            occupied_ticks.add(beat_tick)
        else:
            scheduled.append((beat_tick, 0, main_x[index % len(main_x)], 0, index, None))
            occupied_ticks.add(beat_tick)

        if index in chord_beats:
            # The second note is deliberately well separated from the main
            # note, keeping the two-finger chord readable on a phone.
            chord_x = 0.78 if main_x[index % len(main_x)] < 0.5 else 0.22
            scheduled.append((beat_tick, 0, chord_x, 0, index, None))

    # Add syncopated 8th notes on alternating beats. Do not place them during
    # a hold, chain, or at the end of the excerpt where no measured midpoint
    # exists.
    offbeat_count = 0
    for index in range(count - 1):
        if index % 4 not in (1, 3):
            continue
        tick = index * TIME_BASE + HALF_BEAT
        if tick in occupied_ticks or index in hold_starts or index in chain_starts:
            continue
        scheduled.append(
            (tick, 0, offbeat_x[offbeat_count % len(offbeat_x)], 0, index, None)
        )
        occupied_ticks.add(tick)
        offbeat_count += 1

    # Sort by time before assigning stable IDs and drag links.
    scheduled.sort(key=lambda item: (item[0], item[2], item[1]))
    notes: list[dict[str, Any]] = []
    chain_note_ids: dict[int, list[int]] = defaultdict(list)
    for index, (tick, note_type, x, hold_tick, page_index, chain_slot) in enumerate(scheduled):
        notes.append(
            make_note(
                note_id=index,
                page_index=tick // TIME_BASE,
                tick=tick,
                x=x,
                note_type=note_type,
                hold_tick=hold_tick,
            )
        )
        if chain_slot is not None:
            chain_note_ids[page_index].append(index)

    for chain_ids in chain_note_ids.values():
        for current, following in zip(chain_ids, chain_ids[1:]):
            notes[current]["next_id"] = following

    chart = {
        "format_version": 0,
        "time_base": TIME_BASE,
        "music_offset": round(-float(analysis["analysis"]["first_beat_seconds"]), 6),
        "display_background": False,
        "page_list": pages,
        "tempo_list": measured_tempo_list(beats),
        "event_order_list": [],
        "note_list": notes,
    }
    plan = {
        "beat_count": count,
        "chain_starts": sorted(chain_starts),
        "hold_starts": sorted(hold_starts),
        "chord_beats": sorted(chord_beats),
        "offbeat_count": offbeat_count,
    }
    return chart, plan


def chart_time(tick: int, tempo_list: list[dict[str, Any]]) -> float:
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
            / TIME_BASE
        )
        current_tick = tempo_list[index]["tick"]
        zone = index
    result += (tick - current_tick) * 1e-6 * tempo_list[zone]["value"] / TIME_BASE
    return result


def validate(
    chart: dict[str, Any],
    analysis: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    pages = chart["page_list"]
    tempos = chart["tempo_list"]
    notes = chart["note_list"]
    beats = analysis["beats"]
    require(len(pages) == len(beats), "page count must equal measured beat count")
    require(len(tempos) == len(beats), "tempo count must equal measured beat count")
    require(notes, "chart must contain notes")
    require(all(note["type"] in ALLOWED_NOTE_TYPES for note in notes), "unsupported note type")
    require(len({note["id"] for note in notes}) == len(notes), "note ids are not unique")
    require(all(0 <= note["page_index"] < len(pages) for note in notes), "invalid page index")
    require(all(0.0 <= note["x"] <= 1.0 for note in notes), "note x is outside [0, 1]")
    require(all(page["end_tick"] > page["start_tick"] for page in pages), "page span must be positive")
    require(all(a["tick"] < b["tick"] for a, b in zip(tempos, tempos[1:])), "tempo ticks are not increasing")
    require(all(tempo["value"] > 0 for tempo in tempos), "tempo value must be positive")
    require(all(a["end_tick"] <= b["start_tick"] for a, b in zip(pages, pages[1:])), "pages overlap")
    first_beat = float(analysis["analysis"]["first_beat_seconds"])
    measured = [float(beat["time_seconds"]) - first_beat for beat in beats]
    expected_by_tick = {index * TIME_BASE: time for index, time in enumerate(measured)}
    for index in range(len(measured) - 1):
        expected_by_tick[index * TIME_BASE + HALF_BEAT] = (
            (float(beats[index]["time_seconds"]) + float(beats[index + 1]["time_seconds"])) / 2.0
            - first_beat
        )

    note_times: list[float] = []
    timing_errors: list[float] = []
    note_by_id = {note["id"]: note for note in notes}
    for note in notes:
        tick = int(note["tick"])
        require(tick in expected_by_tick, f"note tick {tick} is not on the measured grid")
        require(note["page_index"] == tick // TIME_BASE, "note page does not match its tick")
        time = chart_time(tick, tempos)
        note_times.append(time)
        timing_errors.append(time - expected_by_tick[tick])
        if note["type"] == 1:
            require(note["hold_tick"] > 0, "hold note must have positive duration")
        if note["type"] in (3, 4) and note["next_id"]:
            require(note["next_id"] in note_by_id, "drag chain points to a missing note")
            require(note["next_id"] > note["id"], "drag chain must move forward")
            require(note_by_id[note["next_id"]]["type"] == 4, "drag head or child must link to a drag child")

    require(all(a <= b for a, b in zip(note_times, note_times[1:])), "note times are not chronological")
    max_error = max(abs(value) for value in timing_errors)
    require(max_error <= 0.005, f"timing drift exceeds tolerance: {max_error:.6f}s")

    by_tick = Counter(int(note["tick"]) for note in notes)
    distinct_times = sorted(set(note_times))
    intervals = [b - a for a, b in zip(distinct_times, distinct_times[1:])]
    type_counts = Counter(str(note["type"]) for note in notes)
    drag_chain_count = sum(1 for note in notes if note["type"] == 3)
    hold_count = type_counts.get("1", 0)
    chord_slots = sum(1 for count in by_tick.values() if count > 1)
    return {
        "status": "ok",
        "candidate": "Luna max-thinking medium",
        "level": "level.json",
        "chart": "chart.medium.json",
        "package": PACKAGE_PATH.name,
        "engine_difficulty_id": "hard",
        "conceptual_difficulty": "medium",
        "measured_beat_count": len(beats),
        "note_count": len(notes),
        "note_density_per_second": round(len(notes) / 210.0, 4),
        "note_density_per_measured_beat": round(len(notes) / len(beats), 4),
        "type_counts": dict(sorted(type_counts.items(), key=lambda item: int(item[0]))),
        "hold_count": hold_count,
        "drag_chain_count": drag_chain_count,
        "chord_slot_count": chord_slots,
        "max_simultaneous_notes": max(by_tick.values()),
        "max_notes_per_page": max(Counter(note["page_index"] for note in notes).values()),
        "offbeat_count": plan["offbeat_count"],
        "min_distinct_note_interval_seconds": round(min(intervals), 6) if intervals else 0.0,
        "mean_distinct_note_interval_seconds": round(sum(intervals) / len(intervals), 6) if intervals else 0.0,
        "chart_duration_seconds": round(note_times[-1], 6),
        "max_measured_grid_error_seconds": round(max_error, 6),
        "mean_measured_grid_error_seconds": round(
            sum(abs(value) for value in timing_errors) / len(timing_errors), 6
        ),
        "structure": {
            "chain_starts": plan["chain_starts"],
            "hold_starts": plan["hold_starts"],
            "chord_beats": plan["chord_beats"],
        },
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_package(level: dict[str, Any], chart: dict[str, Any]) -> None:
    require(AUDIO_PATH.is_file(), f"missing trimmed runtime audio: {AUDIO_PATH}")
    entries = {
        "level.json": json.dumps(level, indent=2, ensure_ascii=False).encode("utf-8") + b"\n",
        "chart.medium.json": json.dumps(chart, indent=2, ensure_ascii=False).encode("utf-8") + b"\n",
        "music.mp3": AUDIO_PATH.read_bytes(),
    }
    with zipfile.ZipFile(PACKAGE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            package.writestr(info, data)


def write_rationale(report: dict[str, Any]) -> None:
    lines = [
        "# Luna medium chart candidate",
        "",
        "This is a separate, reviewable medium candidate produced with the Luna max-thinking pass. It does not replace the canonical easy chart.",
        "",
        "## Engine mapping",
        "",
        "The inherited Cytoid engine exposes `easy`, `hard`, and `extreme` chart ids. This candidate uses `type: hard` and `difficulty: 6` while naming the conceptual tier Medium, so it can be loaded by the current engine without adding a new difficulty identifier.",
        "",
        "## Timing basis",
        "",
        "- Source analysis: `docs/audio/hladini_shakti_excerpt.analysis.json`",
        "- Excerpt: 3:00 to 6:30, 210 seconds",
        "- Timing grid: 358 measured beats with the analysis tempo map",
        "- Added subdivisions: measured midpoints between adjacent tracked beats",
        "- No fixed BPM or guessed millisecond timings are used",
        "",
        "## Pattern design",
        "",
        "- One readable main gesture per measured beat",
        "- Alternating 8th-note syncopations on selected beats",
        "- One-beat holds at regular phrase positions",
        "- Short three-note drag chains every 32 beats",
        "- Two-finger chords at phrase accents, with notes separated across the play area",
        "- At most two simultaneous notes and no subdivision smaller than an 8th note",
        "",
        "## Deterministic report",
        "",
        f"- Notes: {report['note_count']} ({report['note_density_per_second']:.4f}/second)",
        f"- Notes per measured beat: {report['note_density_per_measured_beat']:.4f}",
        f"- Types: {json.dumps(report['type_counts'], sort_keys=True)}",
        f"- Holds: {report['hold_count']}; drag chains: {report['drag_chain_count']}; chord slots: {report['chord_slot_count']}",
        f"- Maximum simultaneous notes: {report['max_simultaneous_notes']}",
        f"- Minimum distinct-note interval: {report['min_distinct_note_interval_seconds']:.6f}s",
        f"- Maximum measured-grid error: {report['max_measured_grid_error_seconds']:.6f}s",
        "",
        "This remains a candidate. Human listening, chart-editor inspection, and Android playtesting are required before promotion.",
        "",
    ]
    RATIONALE_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_validation_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Luna medium candidate validation",
        "",
        "Deterministic validation generated by `build_candidate.py`.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Status | `{report['status']}` |",
        f"| Notes | {report['note_count']} |",
        f"| Note density | {report['note_density_per_second']:.4f}/s |",
        f"| Notes per measured beat | {report['note_density_per_measured_beat']:.4f} |",
        f"| Holds | {report['hold_count']} |",
        f"| Drag chains | {report['drag_chain_count']} |",
        f"| Chord slots | {report['chord_slot_count']} |",
        f"| Maximum simultaneous notes | {report['max_simultaneous_notes']} |",
        f"| Minimum distinct-note interval | {report['min_distinct_note_interval_seconds']:.6f}s |",
        f"| Maximum measured-grid error | {report['max_measured_grid_error_seconds']:.6f}s |",
        "",
        "The structural checks cover C2 page, tempo, note type, id, ordering, and timing-grid invariants. The measured grid is the existing expressive beat analysis plus its deterministic half-beat midpoints.",
        "",
    ]
    VALIDATION_MARKDOWN_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    analysis = load_analysis()
    chart, plan = make_chart(analysis)
    level = {
        "schema_version": 2,
        "version": 1,
        "id": "kiirtaniyas.hladini_excerpt_luna_medium",
        "title": "Hladini Shakti Kiirtana - Excerpt (Luna Medium Candidate)",
        "artist": "Bhuvanesh",
        "charter": "Kiirtaniyas United - Luna candidate",
        "music": {"path": "music.mp3"},
        "music_preview": {"path": "music.mp3"},
        "charts": [
            {
                "type": "hard",
                "name": "Medium (Luna candidate)",
                "difficulty": 6,
                "path": "chart.medium.json",
            }
        ],
    }
    report = validate(chart, analysis, plan)
    write_json(CHART_PATH, chart)
    write_json(LEVEL_PATH, level)
    write_package(level, chart)
    write_json(VALIDATION_PATH, report)
    write_rationale(report)
    write_validation_markdown(report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
