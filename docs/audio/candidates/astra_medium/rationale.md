# Astra medium candidate

This isolated candidate targets a readable medium chart for the 210-second excerpt from 3:00 to 6:30. The inherited engine has no medium identifier, so `level.json` uses `hard`, a provisional numeric rating of 6, and a visible Medium name. No canonical chart or runtime code is changed.

All 358 beat anchors use the existing measured analysis. Integer microseconds preserve its six-decimal timestamps exactly within floating-point precision. Eighth notes are interpolated midpoints of adjacent measured beats, not separately detected onsets. No fixed BPM or clamping is used. The original analysis contains 71 unmatched tracked beats, so exact grid agreement does not establish musical accuracy.

Four-beat scan pages give roughly 2.3 seconds per sweep and distribute notes vertically. A repeating pair of broad lanes supports alternating hands. The opening, ending, and every fourth 16-beat block reduce subdivisions. Those blocks are authored pacing choices, not claims about verified musical phrase boundaries.

Twenty-two one-beat holds fit entirely inside their pages. Eleven short three-node drags reserve their endpoint beat, avoiding an unrelated tap at the drag endpoint. Twenty-one explicit two-tap accents are separated by 0.4 screen width. Chords are marked as siblings. Holds have no intervening taps. No pattern uses a subdivision smaller than half a measured beat.

## Comparison with the existing Luna medium report

| Metric | Astra | Luna |
| --- | ---: | ---: |
| Notes | 529 | 580 |
| Notes per second | 2.5190 | 2.7619 |
| Notes per measured beat | 1.4777 | 1.6201 |
| Holds | 22 | 23 |
| Drag chains | 11 | 11 |
| Simultaneous slots | 21 | 33 |
| Maximum simultaneous notes | 2 | 2 |
| Minimum distinct interval | 0.261224 s | 0.261224 s |
| Mean distinct interval | 0.412876 s | 0.383384 s |
| Maximum measured-grid error | 0.000000 s | 0.000000 s |
| Beats per scan page | 4 | 1 |

The reported notes per page are not directly comparable because page lengths differ. Astra reports all half-beat nodes in `offbeat_count`, including drag children. Luna's generator reports added tap offbeats separately from drag nodes, so compare density and timing intervals instead of treating that field as identical.

## Rebuild and review

Run `python3 docs/audio/candidates/astra_medium/build_candidate.py` from the repository. The package contains `level.json`, `chart.medium.json`, and the existing excerpt as `music.mp3`. ZIP timestamps are fixed for reproducibility.

`validation.json` holds deterministic metrics and checksums. `c2_validator_output.json` records the existing structural validator, called through `validator_adapter.json` because that tool only selects easy charts. The actual packaged level remains hard. Additional candidate checks cover measured-grid alignment, page containment, hold overlap, chord separation, forward drag links, and package contents.

The candidate has not been listened through, inspected in a chart editor, or playtested on Android. Numeric difficulty and pattern comfort remain provisional. Review scan reversals, alternating eighths, and the final partial page before promotion.
