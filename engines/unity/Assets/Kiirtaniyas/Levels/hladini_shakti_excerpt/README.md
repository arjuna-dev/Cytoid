# Hladini Shakti Kiirtana excerpt

This folder contains the first measured C2 chart scaffold and level metadata
for the 3:00 to 6:30 excerpt of the local recording. The original source
recording remains outside the repository. The trimmed 210 second runtime clip
is included in the Unity audio folder and in the built-in level package, with
the source artist credited as Bhuvanesh.

The easy chart is a measured, sparse pulse with restrained four-beat pages. The
medium chart is stored under the inherited C2 `hard` type so the existing engine
can load it, while the navigation menu displays it as Medium. Both charts use a
piecewise tempo map encoded from measured beat intervals and a negative
`music_offset` so their first measured beat follows the excerpt onset. Human
listening review and playtesting are still required before release.

To regenerate the playable `.cytoidlevel` package after reviewing audio
rights:

```bash
python3 tools/audio/package_kiirtan_level.py \
  --source '/Users/alejandrocamus/Downloads/Hladini shakti kiirtana.mp3' \
  --start 180 \
  --duration 210 \
  --level-dir engines/unity/Assets/Kiirtaniyas/Levels/hladini_shakti_excerpt \
  --output engines/unity/Assets/StreamingAssets/Levels/kiirtaniyas.hladini_excerpt.cytoidlevel
```

The package is included for this prototype because the project owner supplied
the recording and confirmed free service use. Recheck the recording license and
attribution before publishing a store build.
