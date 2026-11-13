# Deterministic validation

Status: passed. Run `build_candidate.py` to regenerate the machine-readable `validation.json` and package.

- 529 notes across 90 four-beat pages and 358 measured tempo entries.
- 474 taps, 22 holds, 11 drag heads, 22 drag children.
- 21 simultaneous tap pairs, maximum two notes at one time.
- Measured-grid error below one microsecond, reported as zero at nine decimal places.
- Minimum distinct interval: 0.261224 seconds.
- All notes inside their assigned pages; holds end within their pages and contain no intervening note.
- Every drag has exactly three nodes with forward links and a terminal zero link.
- Simultaneous notes are taps separated by at least 0.3 normalized screen width.
- Package CRC and byte-for-byte comparison of metadata, chart, and audio passed.

The existing easy-only C2 validator was run against a metadata adapter pointing at the same chart. This verifies structural invariants without altering the delivered hard-type metadata. These are static checks, not Unity loading or device playtest results.
