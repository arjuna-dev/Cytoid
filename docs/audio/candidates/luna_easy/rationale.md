# Luna easy candidate

This is an independent easy-chart candidate for the 3:00 to 6:30 excerpt of
`Hladini shakti kiirtana`. It does not replace the canonical chart.

## Mapping decisions

- Preserve the measured, piecewise tempo map from
  `docs/audio/hladini_shakti_excerpt.analysis.json`.
- Select every second measured beat, starting at beat 0. This produces one
  simple tap about every 1.17 seconds while retaining expressive timing.
- Use only C2 type `0` tap notes. There are no holds, siblings, or new note
  semantics.
- Use 179 two-beat pages with alternating scan direction and a restrained
  horizontal position pattern. The movement stays readable for a first
  playthrough.
- Keep `music_offset` at `-0.267029`, matching the first measured beat.

## Deterministic comparison metrics

- Notes: 179 of 358 measured beats, density 0.5.
- Pages: 179. Tempo entries: 358.
- Note gaps: 1.084615 to 1.254670 seconds, mean 1.172608 seconds.
- Timing error against the selected measured beats: 0.000000 seconds after
  C2 tick conversion.
- Note types: 179 basic taps. Holds: 0. Siblings: 0.

The timing and schema checks are recorded in `validation.json`. Human listening
review and device playtesting are still required before choosing a canonical
chart.

## Rebuild and package

Regenerate the candidate chart and metadata:

```bash
python3 docs/audio/candidates/luna_easy/build_candidate.py
python3 docs/audio/candidates/luna_easy/validate_candidate.py
```

Build the local `.cytoidlevel` package with the supplied source recording:

```bash
python3 tools/audio/package_kiirtan_level.py \
  --source '/Users/alejandrocamus/Downloads/Hladini shakti kiirtana.mp3' \
  --start 180 \
  --duration 210 \
  --level-dir docs/audio/candidates/luna_easy \
  --output docs/audio/candidates/luna_easy/kiirtaniyas.hladini_excerpt_luna_easy.cytoidlevel
```

The source MP3 remains outside the repository. Recheck attribution and
recording rights before any store release.
