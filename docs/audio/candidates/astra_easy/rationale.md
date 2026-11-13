# Astra easy candidate

This isolated difficulty-3 draft uses 184 ordinary clicks over the measured 210-second Hladini Shakti excerpt. It preserves the full 358-entry measured tempo map with no global-BPM approximation or interval clamping. It changes note selection and spatial phrasing only. Canonical level files were not edited.

The main pulse is every other measured beat. From 70 to 190 seconds, an occasional additional measured-onset beat forms a short three-note phrase, at most once per 16 beats. These windows are broad arrangement cues from the analysis, not confirmed musical phrase labels. This adds modest variety without holds, flicks, drags, simultaneous notes, or invented timing. The first note is at 2.589025 seconds to give entry time; the last is at 206.634376 seconds to leave a quiet ending.

Four-beat pages slow the scan line and show predominantly two notes per page. Horizontal positions move in a restrained central band, 0.34 to 0.64, with a maximum adjacent move of 0.18 screen width. These choices aim for an approachable reading workload. Difficulty 3 is provisional until device playtesting.

## Deterministic validation

- Repository C2 validator: passed for level metadata and chart structure.
- Additional checks: consecutive IDs, click-only semantics, note membership within pages, continuous pages, chronological timing, and a minimum spacing floor all passed.
- All 358 measured beat positions and all 184 selected notes agree with the supplied analysis to below 0.000001 milliseconds, within floating-point arithmetic precision. This measures agreement with the analysis, not independently verified acoustic onset accuracy.
- Density: 0.876 notes per second over the full excerpt.
- Minimum note interval: 0.578935 seconds. Maximum: 1.254670 seconds.
- Selected notes: 147 matched onsets and 37 predicted pulse positions. Predicted positions retain the measured pulse continuity and require listening review.
- Package CRC and byte-for-byte identity of packaged chart and metadata passed. Package contains exactly level.json, chart.easy.json, and music.mp3.
- Packaged audio decodes to 210.000979 seconds at 48 kHz stereo. The sub-millisecond difference is within MP3 decoding tolerance.

The base validator's analysis flag assumes one note per measured beat and is unsuitable for this sparse selection. The candidate builder instead validates the selected beat indices and independently checks every measured beat against the complete tempo map. The full machine-readable report is in validation.json.

Rebuild and revalidate from the repository root:

```sh
python3 docs/audio/candidates/astra_easy/build_candidate.py
```

The package is a local review artifact containing the requested source excerpt. It has not been published. Human listening, chart-editor inspection, and gameplay validation remain pending. No musical phrase or onset certainty beyond the supplied measured analysis is claimed.
