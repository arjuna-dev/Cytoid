#!/usr/bin/env python3
"""Build a local Cytoid level package with a trimmed source recording.

The source recording is read by ffmpeg and is never copied into the
repository. The output package should normally be written outside the
repository until audio rights and attribution are confirmed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def run_checked(args: list[str]) -> None:
    try:
        subprocess.run(args, check=True)
    except FileNotFoundError as error:
        raise SystemExit(f"Required command is not installed: {args[0]}") from error
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"Command failed with exit code {error.returncode}: {' '.join(args)}") from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--start", type=float, default=180.0)
    parser.add_argument("--duration", type=float, default=210.0)
    parser.add_argument("--level-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.is_file():
        raise SystemExit(f"Source audio does not exist: {args.source}")
    if args.start < 0.0 or args.duration <= 0.0:
        raise SystemExit("--start must be non-negative and --duration must be positive")
    level_path = args.level_dir / "level.json"
    if not level_path.is_file():
        raise SystemExit(f"Missing level asset: {level_path}")
    try:
        level = json.loads(level_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid level metadata: {level_path}: {error}") from error

    charts = level.get("charts")
    if not isinstance(charts, list) or not charts:
        raise SystemExit(f"Level has no charts: {level_path}")
    chart_names: list[str] = []
    for chart in charts:
        chart_path = chart.get("path") if isinstance(chart, dict) else None
        if not isinstance(chart_path, str) or not chart_path or chart_path.startswith("/"):
            raise SystemExit(f"Invalid chart path in {level_path}: {chart_path!r}")
        resolved = (args.level_dir / chart_path).resolve()
        if args.level_dir.resolve() not in resolved.parents:
            raise SystemExit(f"Chart path escapes level directory: {chart_path}")
        if not resolved.is_file():
            raise SystemExit(f"Missing level asset: {resolved}")
        chart_names.append(chart_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kiirtan-level-") as temp_name:
        temp_dir = Path(temp_name)
        run_checked(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                f"{args.start:.6f}",
                "-i",
                str(args.source),
                "-t",
                f"{args.duration:.6f}",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(temp_dir / "music.mp3"),
            ]
        )
        shutil.copy2(level_path, temp_dir / "level.json")
        for chart_name in chart_names:
            chart_destination = temp_dir / chart_name
            chart_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.level_dir / chart_name, chart_destination)
        with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as package:
            package.write(temp_dir / "level.json", arcname="level.json")
            for chart_name in chart_names:
                package.write(temp_dir / chart_name, arcname=chart_name)
            package.write(temp_dir / "music.mp3", arcname="music.mp3")

    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
