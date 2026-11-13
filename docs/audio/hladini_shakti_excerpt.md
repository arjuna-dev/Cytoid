# Hladini Shakti Kiirtana excerpt analysis

This is a local, source-safe timing analysis for the first Kiirtaniyas United song prototype.

## Source and excerpt

- Source: `/Users/alejandrocamus/Downloads/Hladini shakti kiirtana.mp3`
- Artist tag: Bhuvanesh
- Source duration: 622.201917 seconds
- Excerpt: 180.000 to 390.000 seconds
- Excerpt duration: 210.000 seconds
- The source audio remains outside the repository.

## Measured pulse

- Global estimate: 101.400 BPM
- Autocorrelation confidence: 0.6468
- Tracked beats: 358
- First tracked beat: 0.267029 seconds into the excerpt
- Last tracked beat: 209.594921 seconds into the excerpt
- Median interval: 0.587180 seconds
- Interval standard deviation: 0.016406 seconds
- Beats predicted without a matched onset: 71

### Tempo windows

| Excerpt window | Estimated BPM | Correlation |
| --- | ---: | ---: |
| 0s to 60s | 101.400 | 0.6281 |
| 60s to 120s | 101.300 | 0.6686 |
| 120s to 180s | 103.300 | 0.7130 |
| 180s to 210s | 103.300 | 0.6441 |

### Phrase candidates

- 20.0s, change strength 1.2497, candidate_for_human_review
- 40.0s, change strength 1.3976, candidate_for_human_review
- 70.0s, change strength 3.3467, candidate_for_human_review
- 100.0s, change strength 1.9561, candidate_for_human_review
- 130.0s, change strength 1.3041, candidate_for_human_review
- 150.0s, change strength 1.3385, candidate_for_human_review
- 170.0s, change strength 0.9237, candidate_for_human_review
- 190.0s, change strength 1.8321, candidate_for_human_review

## Chart status

The runtime package contains a sparse measured easy chart and a denser measured
medium chart. The medium chart uses the inherited C2 `hard` type so it can load
without adding a new difficulty identifier. Both remain subject to human
listening review and Android playtesting.

- Easy chart: `engines/unity/Assets/Kiirtaniyas/Levels/hladini_shakti_excerpt/chart.easy.json`
- Medium chart: `engines/unity/Assets/Kiirtaniyas/Levels/hladini_shakti_excerpt/chart.hard.json`

To rebuild the analysis after the source recording changes:

```bash
python3 tools/audio/analyze_kiirtan_excerpt.py \
  --source '/Users/alejandrocamus/Downloads/Hladini shakti kiirtana.mp3' \
  --start 180.000 \
  --duration 210.000 \
  --analysis-json docs/audio/hladini_shakti_excerpt.analysis.json \
  --analysis-markdown docs/audio/hladini_shakti_excerpt.md \
  --chart docs/audio/generated/hladini_shakti_scaffold.chart.easy.json
```

The command writes a temporary scaffold under `docs/audio/generated/`; it does
not overwrite the promoted runtime charts.
