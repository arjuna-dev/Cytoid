#!/usr/bin/env python3
"""Measure an expressive kiirtan excerpt and emit a first C2 chart.

The tool deliberately keeps the audio outside the repository. It decodes a
local source with ffmpeg, measures spectral onsets, follows the recurring
pulse, and writes a tempo map with one measured beat interval per C2 beat.
The generated chart is a timing scaffold for human review, not a claim that
all musical accents have been charted.

Only Python's standard library, numpy, ffmpeg, and ffprobe are required.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

import numpy as np


DEFAULT_SAMPLE_RATE = 22050
DEFAULT_FFT_SIZE = 2048
DEFAULT_HOP_SIZE = 256
DEFAULT_TIME_BASE = 480
MIN_BPM = 80.0
MAX_BPM = 120.0


def run_checked(args: Sequence[str], *, capture_output: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run a local command and surface a useful error on failure."""

    try:
        return subprocess.run(
            list(args),
            check=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"Required command is not installed: {args[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip() if error.stderr else ""
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{detail}") from error


def probe_source(source: Path) -> dict[str, Any]:
    """Read stable source metadata without copying the source audio."""

    result = run_checked(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:format_tags=title,artist,album",
            "-of",
            "json",
            str(source),
        ]
    )
    raw = json.loads(result.stdout.decode("utf-8"))
    fmt = raw.get("format", {})
    tags = fmt.get("tags", {}) or {}
    duration = fmt.get("duration")
    metadata: dict[str, Any] = {
        "path": str(source),
        "title": tags.get("title"),
        "artist": tags.get("artist"),
        "album": tags.get("album"),
        "duration_seconds": float(duration) if duration is not None else None,
    }
    return metadata


def decode_excerpt(source: Path, start_seconds: float, duration_seconds: float, sample_rate: int) -> np.ndarray:
    """Decode a mono floating point excerpt through ffmpeg."""

    result = run_checked(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{start_seconds:.6f}",
            "-i",
            str(source),
            "-t",
            f"{duration_seconds:.6f}",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "pipe:1",
        ]
    )
    samples = np.frombuffer(result.stdout, dtype="<f4").astype(np.float32, copy=False)
    if samples.size == 0:
        raise RuntimeError("ffmpeg decoded no samples from the requested excerpt")
    expected = max(1, round(duration_seconds * sample_rate))
    # A seek at the end of a source can produce a few missing samples. Trim
    # only excess samples and let a materially short decode fail loudly.
    if samples.size < expected * 0.98:
        raise RuntimeError(
            f"Decoded excerpt is unexpectedly short: {samples.size / sample_rate:.3f}s "
            f"for requested {duration_seconds:.3f}s"
        )
    return samples[:expected]


def make_frames(samples: np.ndarray, fft_size: int, hop_size: int) -> np.ndarray:
    """Return a strided frame matrix without a second full audio copy."""

    if samples.size < fft_size:
        samples = np.pad(samples, (0, fft_size - samples.size))
    frame_count = 1 + (samples.size - fft_size) // hop_size
    return np.lib.stride_tricks.as_strided(
        samples,
        shape=(frame_count, fft_size),
        strides=(samples.strides[0] * hop_size, samples.strides[0]),
        writeable=False,
    )


def spectral_onset_envelope(
    samples: np.ndarray,
    sample_rate: int,
    fft_size: int = DEFAULT_FFT_SIZE,
    hop_size: int = DEFAULT_HOP_SIZE,
) -> tuple[np.ndarray, np.ndarray]:
    """Calculate a normalized positive spectral-flux onset envelope."""

    frames = make_frames(samples, fft_size, hop_size)
    window = np.hanning(fft_size).astype(np.float32)
    magnitudes = np.abs(np.fft.rfft(frames * window, n=fft_size, axis=1))
    log_magnitudes = np.log1p(magnitudes * 20.0)
    flux = np.maximum(0.0, np.diff(log_magnitudes, axis=0)).sum(axis=1)
    if flux.size == 0:
        flux = np.zeros(1, dtype=np.float32)
    else:
        flux = np.concatenate(([flux[0]], flux))
    # A short smoothing pass avoids selecting individual FFT-bin spikes while
    # preserving the roughly half-second pulse in this recording.
    flux = np.convolve(flux, np.ones(3, dtype=np.float32) / 3.0, mode="same")
    low, high = np.percentile(flux, [10.0, 95.0])
    normalized = np.clip((flux - low) / max(float(high - low), 1e-9), 0.0, 1.0)
    frame_times = np.arange(normalized.size, dtype=np.float64) * hop_size / float(sample_rate)
    return frame_times, normalized.astype(np.float32)


def _interpolated_correlation(values: np.ndarray, lag: float) -> float:
    """Correlation at a fractional frame lag."""

    lag_floor = int(math.ceil(lag))
    usable = len(values) - lag_floor - 1
    if usable <= 2:
        return 0.0
    indexes = np.arange(usable, dtype=np.float64)
    shifted = indexes + lag
    lower = np.floor(shifted).astype(np.int64)
    fraction = shifted - lower
    right = values[lower] * (1.0 - fraction) + values[lower + 1] * fraction
    return float(np.mean(values[:usable] * right))


def estimate_bpm(
    frame_times: np.ndarray,
    onset: np.ndarray,
    start_seconds: float,
    end_seconds: float,
    sample_rate: int,
    hop_size: int,
) -> tuple[float, float]:
    """Estimate pulse BPM and correlation confidence in a time window."""

    start = max(0, int(np.searchsorted(frame_times, start_seconds, side="left")))
    end = min(len(onset), int(np.searchsorted(frame_times, end_seconds, side="left")))
    values = onset[start:end].astype(np.float64)
    if values.size < 8:
        return 0.0, 0.0
    values -= values.mean()
    standard_deviation = values.std()
    if standard_deviation <= 1e-9:
        return 0.0, 0.0
    values /= standard_deviation
    bpms = np.linspace(MIN_BPM, MAX_BPM, 401)
    correlations = np.array(
        [
            _interpolated_correlation(values, 60.0 / bpm * sample_rate / hop_size)
            for bpm in bpms
        ]
    )
    best = int(np.argmax(correlations))
    return float(bpms[best]), float(correlations[best])


def onset_peaks(
    frame_times: np.ndarray,
    onset: np.ndarray,
    *,
    threshold: float = 0.4,
    minimum_distance_seconds: float = 0.18,
) -> tuple[np.ndarray, np.ndarray]:
    """Find local onset peaks with deterministic non-maximum suppression."""

    if len(onset) < 9:
        return np.empty(0, dtype=np.float64), np.empty(0, dtype=np.float32)
    local = np.flatnonzero(
        (onset[4:-4] >= onset[3:-5]) & (onset[4:-4] >= onset[5:-3])
    ) + 4
    local = local[onset[local] >= threshold]
    selected: list[int] = []
    minimum_distance_frames = minimum_distance_seconds / max(frame_times[1] - frame_times[0], 1e-9)
    for index in sorted(local.tolist(), key=lambda item: float(onset[item]), reverse=True):
        if all(abs(index - other) >= minimum_distance_frames for other in selected):
            selected.append(index)
    selected.sort()
    indexes = np.asarray(selected, dtype=np.int64)
    return frame_times[indexes], onset[indexes]


def track_beats(
    frame_times: np.ndarray,
    onset: np.ndarray,
    *,
    duration_seconds: float,
    sample_rate: int,
    hop_size: int,
) -> list[dict[str, Any]]:
    """Follow the pulse with a small phase-locked onset tracker.

    The tracker starts on the strongest onset in the first second, searches
    for the nearest plausible onset on each beat, and updates its period only
    for intervals in the expected beat range. Weak or missing onsets retain
    the predicted beat time, which prevents a vocal flourish from doubling
    the chart tempo.
    """

    peak_times, peak_strengths = onset_peaks(frame_times, onset)
    if len(peak_times) < 4:
        raise RuntimeError("Could not find enough onset peaks to track a beat grid")

    global_bpm, _ = estimate_bpm(
        frame_times,
        onset,
        0.0,
        min(duration_seconds, 30.0),
        sample_rate,
        hop_size,
    )
    if global_bpm <= 0.0:
        global_bpm = 101.0
    period = 60.0 / global_bpm

    first_candidates = np.flatnonzero(peak_times < min(1.0, duration_seconds))
    if len(first_candidates) == 0:
        raise RuntimeError("Could not locate an initial beat in the first second")
    first_index = int(first_candidates[np.argmax(peak_strengths[first_candidates])])
    beats: list[dict[str, Any]] = [
        {
            "index": 0,
            "time_seconds": float(peak_times[first_index]),
            "onset_strength": float(peak_strengths[first_index]),
            "matched_to_onset": True,
        }
    ]

    while True:
        previous_time = float(beats[-1]["time_seconds"])
        expected = previous_time + period
        if expected > duration_seconds:
            break

        left = int(np.searchsorted(peak_times, expected - 0.14, side="left"))
        right = int(np.searchsorted(peak_times, expected + 0.14, side="right"))
        matched = False
        strength = 0.0
        actual = expected
        if right > left:
            candidates = np.arange(left, right, dtype=np.int64)
            distance = (peak_times[candidates] - expected) / 0.10
            scores = peak_strengths[candidates] - 0.8 * distance * distance
            candidate = int(candidates[np.argmax(scores)])
            candidate_time = float(peak_times[candidate])
            candidate_interval = candidate_time - previous_time
            if 0.52 <= candidate_interval <= 0.66:
                actual = candidate_time
                strength = float(peak_strengths[candidate])
                matched = True

        interval = actual - previous_time
        if matched:
            alpha = 0.18 + 0.20 * strength
            period = float(np.clip((1.0 - alpha) * period + alpha * interval, 0.54, 0.64))

        beats.append(
            {
                "index": len(beats),
                "time_seconds": float(actual),
                "onset_strength": strength,
                "matched_to_onset": matched,
                "interval_seconds": float(interval),
            }
        )

    if len(beats) < 16:
        raise RuntimeError(f"Beat tracker produced too few beats: {len(beats)}")
    return beats


def feature_phrase_candidates(
    samples: np.ndarray,
    frame_times: np.ndarray,
    onset: np.ndarray,
    sample_rate: int,
    duration_seconds: float,
) -> list[dict[str, Any]]:
    """Return structural change candidates for human phrase review."""

    # The phrase detector is intentionally conservative. It compares ten
    # second windows using RMS, onset density, and spectral centroid, then
    # retains changes at least 20 seconds apart. These are candidates, not
    # asserted musical downbeats.
    window_seconds = 10.0
    starts = np.arange(0.0, max(duration_seconds - window_seconds, 0.0) + 1e-6, window_seconds)
    features: list[list[float]] = []
    fft_size = DEFAULT_FFT_SIZE
    hop_size = DEFAULT_HOP_SIZE
    frames = make_frames(samples, fft_size, hop_size)
    magnitudes = np.abs(np.fft.rfft(frames * np.hanning(fft_size), n=fft_size, axis=1))
    frequencies = np.fft.rfftfreq(fft_size, 1.0 / sample_rate)
    centroid = (magnitudes * frequencies).sum(axis=1) / np.maximum(magnitudes.sum(axis=1), 1e-9)
    for start in starts:
        end = start + window_seconds
        sample_start = int(round(start * sample_rate))
        sample_end = min(len(samples), int(round(end * sample_rate)))
        part = samples[sample_start:sample_end]
        frame_start = int(np.searchsorted(frame_times, start, side="left"))
        frame_end = int(np.searchsorted(frame_times, end, side="left"))
        features.append(
            [
                float(np.sqrt(np.mean(part * part))) if len(part) else 0.0,
                float(np.mean(onset[frame_start:frame_end])) if frame_end > frame_start else 0.0,
                float(np.mean(centroid[frame_start:frame_end])) if frame_end > frame_start else 0.0,
            ]
        )
    if len(features) < 3:
        return []

    values = np.asarray(features, dtype=np.float64)
    scale = np.maximum(values.std(axis=0), 1e-9)
    normalized = (values - values.mean(axis=0)) / scale
    changes = np.linalg.norm(np.diff(normalized, axis=0), axis=1)
    candidates = []
    for index in np.argsort(changes)[::-1]:
        time = float(starts[index + 1])
        if time < 20.0 or time > duration_seconds - 20.0:
            continue
        if all(abs(time - item["time_seconds"]) >= 20.0 for item in candidates):
            candidates.append(
                {
                    "time_seconds": time,
                    "change_strength": round(float(changes[index]), 4),
                    "review_status": "candidate_for_human_review",
                }
            )
    candidates.sort(key=lambda item: item["time_seconds"])
    return candidates


def make_tempo_list(beats: Sequence[dict[str, Any]], time_base: int) -> list[dict[str, Any]]:
    """Encode each measured beat interval as a C2 tempo segment."""

    intervals = [float(beats[i + 1]["time_seconds"]) - float(beats[i]["time_seconds"]) for i in range(len(beats) - 1)]
    if not intervals:
        return [{"tick": 0, "value": 600000}]
    values = [max(450000, min(800000, int(round(interval * 1_000_000)))) for interval in intervals]
    values.append(values[-1])
    return [
        {"tick": index * time_base, "value": value}
        for index, value in enumerate(values)
    ]


def make_chart(beats: Sequence[dict[str, Any]], *, time_base: int = DEFAULT_TIME_BASE) -> dict[str, Any]:
    """Create an easy first-pass C2 chart from the measured beat grid."""

    count = len(beats)
    page_list = [
        {
            "start_tick": index * time_base,
            "end_tick": (index + 1) * time_base,
            "scan_line_direction": 1 if index % 2 == 0 else -1,
        }
        for index in range(count)
    ]
    x_pattern = (0.50, 0.30, 0.70, 0.42, 0.58, 0.25, 0.75, 0.50)
    notes = [
        {
            "page_index": index,
            "type": 0,
            "id": index,
            "tick": index * time_base,
            "x": x_pattern[index % len(x_pattern)],
            "has_sibling": False,
            "hold_tick": 0,
            "next_id": 0,
            "is_forward": False,
            "approach_rate": 1.0,
        }
        for index in range(count)
    ]
    first_beat = float(beats[0]["time_seconds"])
    return {
        "format_version": 0,
        "time_base": time_base,
        "music_offset": round(-first_beat, 6),
        "display_background": False,
        "page_list": page_list,
        "tempo_list": make_tempo_list(beats, time_base),
        "event_order_list": [],
        "note_list": notes,
    }


def summarize(
    source_metadata: dict[str, Any],
    *,
    start_seconds: float,
    duration_seconds: float,
    sample_rate: int,
    fft_size: int,
    hop_size: int,
    frame_times: np.ndarray,
    onset: np.ndarray,
    samples: np.ndarray,
    beats: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Build the reviewable analysis document."""

    segment_windows = [(0.0, 60.0), (60.0, 120.0), (120.0, 180.0), (180.0, duration_seconds)]
    tempo_segments = []
    for start, end in segment_windows:
        if start >= duration_seconds:
            continue
        clipped_end = min(end, duration_seconds)
        bpm, confidence = estimate_bpm(frame_times, onset, start, clipped_end, sample_rate, hop_size)
        tempo_segments.append(
            {
                "start_seconds": start,
                "end_seconds": clipped_end,
                "estimated_bpm": round(bpm, 3),
                "autocorrelation_confidence": round(confidence, 4),
            }
        )

    intervals = np.diff([float(item["time_seconds"]) for item in beats])
    first_time = float(beats[0]["time_seconds"])
    last_time = float(beats[-1]["time_seconds"])
    global_bpm, global_confidence = estimate_bpm(
        frame_times,
        onset,
        0.0,
        duration_seconds,
        sample_rate,
        hop_size,
    )
    phrase_candidates = feature_phrase_candidates(
        samples,
        frame_times,
        onset,
        sample_rate,
        duration_seconds,
    )
    return {
        "schema_version": 1,
        "source": {
            **source_metadata,
            "excerpt_start_seconds": start_seconds,
            "excerpt_end_seconds": start_seconds + duration_seconds,
            "excerpt_duration_seconds": duration_seconds,
            "source_audio_copied_to_repository": False,
        },
        "analysis": {
            "method": "mono spectral flux with phase-locked onset tracking",
            "sample_rate": sample_rate,
            "fft_size": fft_size,
            "hop_size": hop_size,
            "global_bpm_estimate": round(global_bpm, 3),
            "global_autocorrelation_confidence": round(global_confidence, 4),
            "tempo_segments": tempo_segments,
            "beat_count": len(beats),
            "first_beat_seconds": round(first_time, 6),
            "last_beat_seconds": round(last_time, 6),
            "median_beat_interval_seconds": round(float(np.median(intervals)), 6),
            "mean_beat_interval_seconds": round(float(np.mean(intervals)), 6),
            "beat_interval_std_seconds": round(float(np.std(intervals)), 6),
            "unmatched_beat_count": sum(1 for beat in beats if not beat.get("matched_to_onset", False)),
            "phrase_boundaries": phrase_candidates,
            "review_notes": [
                "The beat grid is a measured timing scaffold and needs human listening review before release.",
                "Phrase boundaries are structural candidates, not asserted downbeats.",
                "The C2 chart intentionally uses one click per tracked beat and no new kiirtan note semantics.",
            ],
        },
        "beats": [
            {
                "index": int(item["index"]),
                "time_seconds": round(float(item["time_seconds"]), 6),
                "interval_seconds": round(float(item.get("interval_seconds", 0.0)), 6),
                "onset_strength": round(float(item.get("onset_strength", 0.0)), 4),
                "matched_to_onset": bool(item.get("matched_to_onset", False)),
            }
            for item in beats
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, analysis: dict[str, Any], chart_path: Path | None) -> None:
    source = analysis["source"]
    result = analysis["analysis"]
    lines = [
        "# Hladini Shakti Kiirtana excerpt analysis",
        "",
        "This is a local, source-safe timing analysis for the first Kiirtaniyas United song prototype.",
        "",
        "## Source and excerpt",
        "",
        f"- Source: `{source['path']}`",
        f"- Artist tag: {source.get('artist') or 'unknown'}",
        f"- Source duration: {source.get('duration_seconds') or 'unknown'} seconds",
        f"- Excerpt: {source['excerpt_start_seconds']:.3f} to {source['excerpt_end_seconds']:.3f} seconds",
        f"- Excerpt duration: {source['excerpt_duration_seconds']:.3f} seconds",
        "- The source audio remains outside the repository.",
        "",
        "## Measured pulse",
        "",
        f"- Global estimate: {result['global_bpm_estimate']:.3f} BPM",
        f"- Autocorrelation confidence: {result['global_autocorrelation_confidence']:.4f}",
        f"- Tracked beats: {result['beat_count']}",
        f"- First tracked beat: {result['first_beat_seconds']:.6f} seconds into the excerpt",
        f"- Last tracked beat: {result['last_beat_seconds']:.6f} seconds into the excerpt",
        f"- Median interval: {result['median_beat_interval_seconds']:.6f} seconds",
        f"- Interval standard deviation: {result['beat_interval_std_seconds']:.6f} seconds",
        f"- Beats predicted without a matched onset: {result['unmatched_beat_count']}",
        "",
        "### Tempo windows",
        "",
        "| Excerpt window | Estimated BPM | Correlation |",
        "| --- | ---: | ---: |",
    ]
    for segment in result["tempo_segments"]:
        lines.append(
            f"| {segment['start_seconds']:.0f}s to {segment['end_seconds']:.0f}s | "
            f"{segment['estimated_bpm']:.3f} | {segment['autocorrelation_confidence']:.4f} |"
        )
    lines.extend(["", "### Phrase candidates", ""])
    if result["phrase_boundaries"]:
        for candidate in result["phrase_boundaries"]:
            lines.append(
                f"- {candidate['time_seconds']:.1f}s, change strength {candidate['change_strength']:.4f}, "
                f"{candidate['review_status']}"
            )
    else:
        lines.append("- No conservative phrase candidate was detected.")
    lines.extend([
        "",
        "## Chart status",
        "",
        "The generated C2 chart is a temporary easy timing scaffold with one click per tracked beat. Runtime charts are authored separately from this measured analysis and remain subject to human listening review and playtesting.",
    ])
    if chart_path is not None:
        lines.append(f"- Chart: `{chart_path}`")
    lines.extend([
        "",
        "To rebuild the analysis after the source recording changes:",
        "",
        "```bash",
        "python3 tools/audio/analyze_kiirtan_excerpt.py \\",
        f"  --source '{source['path']}' \\",
        f"  --start {source['excerpt_start_seconds']:.3f} \\",
        f"  --duration {source['excerpt_duration_seconds']:.3f} \\",
        "  --analysis-json docs/audio/hladini_shakti_excerpt.analysis.json \\",
        "  --analysis-markdown docs/audio/hladini_shakti_excerpt.md \\",
        "  --chart docs/audio/generated/hladini_shakti_scaffold.chart.easy.json",
        "```",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Local audio file. It is read but never copied.")
    parser.add_argument("--start", type=float, default=180.0, help="Excerpt start in source seconds.")
    parser.add_argument("--duration", type=float, default=210.0, help="Excerpt duration in seconds.")
    parser.add_argument("--analysis-json", type=Path, required=True)
    parser.add_argument("--analysis-markdown", type=Path)
    parser.add_argument("--chart", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.start < 0.0 or args.duration <= 0.0:
        raise SystemExit("--start must be non-negative and --duration must be positive")
    if not args.source.is_file():
        raise SystemExit(f"Source audio does not exist: {args.source}")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe must be installed")

    source_metadata = probe_source(args.source)
    samples = decode_excerpt(args.source, args.start, args.duration, DEFAULT_SAMPLE_RATE)
    frame_times, onset = spectral_onset_envelope(samples, DEFAULT_SAMPLE_RATE)
    beats = track_beats(
        frame_times,
        onset,
        duration_seconds=args.duration,
        sample_rate=DEFAULT_SAMPLE_RATE,
        hop_size=DEFAULT_HOP_SIZE,
    )
    analysis = summarize(
        source_metadata,
        start_seconds=args.start,
        duration_seconds=args.duration,
        sample_rate=DEFAULT_SAMPLE_RATE,
        fft_size=DEFAULT_FFT_SIZE,
        hop_size=DEFAULT_HOP_SIZE,
        frame_times=frame_times,
        onset=onset,
        samples=samples,
        beats=beats,
    )
    chart = make_chart(beats)
    write_json(args.analysis_json, analysis)
    write_json(args.chart, chart)
    if args.analysis_markdown:
        write_markdown(args.analysis_markdown, analysis, args.chart)
    print(
        json.dumps(
            {
                "analysis_json": str(args.analysis_json),
                "chart": str(args.chart),
                "beat_count": len(beats),
                "first_beat_seconds": beats[0]["time_seconds"],
                "last_beat_seconds": beats[-1]["time_seconds"],
                "music_offset": chart["music_offset"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
