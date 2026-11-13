# Luna medium chart candidate

This is a separate, reviewable medium candidate produced with the Luna max-thinking pass. It does not replace the canonical easy chart.

## Engine mapping

The inherited Cytoid engine exposes `easy`, `hard`, and `extreme` chart ids. This candidate uses `type: hard` and `difficulty: 6` while naming the conceptual tier Medium, so it can be loaded by the current engine without adding a new difficulty identifier.

## Timing basis

- Source analysis: `docs/audio/hladini_shakti_excerpt.analysis.json`
- Excerpt: 3:00 to 6:30, 210 seconds
- Timing grid: 358 measured beats with the analysis tempo map
- Added subdivisions: measured midpoints between adjacent tracked beats
- No fixed BPM or guessed millisecond timings are used

## Pattern design

- One readable main gesture per measured beat
- Alternating 8th-note syncopations on selected beats
- One-beat holds at regular phrase positions
- Short three-note drag chains every 32 beats
- Two-finger chords at phrase accents, with notes separated across the play area
- At most two simultaneous notes and no subdivision smaller than an 8th note

## Deterministic report

- Notes: 580 (2.7619/second)
- Notes per measured beat: 1.6201
- Types: {"0": 524, "1": 23, "3": 11, "4": 22}
- Holds: 23; drag chains: 11; chord slots: 33
- Maximum simultaneous notes: 2
- Minimum distinct-note interval: 0.261224s
- Maximum measured-grid error: 0.000000s

This remains a candidate. Human listening, chart-editor inspection, and Android playtesting are required before promotion.
