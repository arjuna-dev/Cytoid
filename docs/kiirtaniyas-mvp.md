# Kiirtaniyas United first vertical slice

The first slice is a real-time Unity presentation scene driven by the 3:00 to
6:30 excerpt of `Hladini shakti kiirtana`. It can run by itself for visual
tuning, and the standalone Android menu build now loads it additively over the
inherited Cytoid `Game` scene during chart play.

## Runtime stages

The stage director follows the 210 second AudioSource clock. The default markers
are deliberately easy to retune in the Inspector or in
`KiirtanMvpSceneBuilder.cs`:

| Stage | Excerpt time | Presentation |
| --- | ---: | --- |
| Intimate | 0:00 | Courtyard, central table, one visible singer plus MC |
| Heavenly | 0:52.5 | Warmer light, fireflies, and a small gathering |
| Cosmic space | 1:45 | Starfield and cool blue atmosphere |
| Cosmic fractal | 2:37.5 | Sacred geometry over black with pulsing color |
| Solo cosmic | 3:19.5 | All other singers disappear and the MC floats alone |

The MC and singers orbit the table clockwise on the XZ plane. Singer counts are
1, 2, 3, 8, and 0 for the five stages. This is background choreography, not a
new note mechanic.

## Source and runtime assets

- Blender source: `art/blender/kiirtaniyas_mvp.blend`
- Rebuildable Blender MCP script: `art/blender/build_mvp.py`
- Reusable Unity world prefab: `Assets/Kiirtaniyas/Art/KiirtanMvpWorld.prefab`
- Unity models and Blender-authored dance clips: `Assets/Kiirtaniyas/Art/Models/`
- Reference-led singer textures: `Assets/Kiirtaniyas/Art/Textures/KU_FaceRaised_Albedo.png` and `KU_FaceJoined_Albedo.png`
- Trimmed Unity clip: `Assets/Kiirtaniyas/Audio/Hladini_shakti_excerpt.mp3`
- Built-in package: `Assets/StreamingAssets/Levels/kiirtaniyas.hladini_excerpt.cytoidlevel`
- Measured easy and medium charts and analysis: `Assets/Kiirtaniyas/Levels/hladini_shakti_excerpt/` and `docs/audio/`
- Candidate comparison: `docs/audio/candidates/luna_easy/`, `luna_medium/`, `astra_easy/`, and `astra_medium/`
- Menu scene: `Assets/Scenes/Navigation.unity`, built with `KiirtanMvpBuild.BuildAndroidMenuBatch`
- Gameplay composition: `Assets/Scripts/Kiirtaniyas/Visual/KiirtanGameplayVisualLoader.cs`

## Chart candidate comparison

All four candidates use the measured tempo map. The Astra pair is promoted in
the built-in package because it leaves a gentler easy opening and gives the
medium chart four-beat scan pages with fewer simultaneous accents.

| Candidate | Notes | Density | Holds | Drag chains | Chord slots | Minimum interval |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna easy | 179 | 0.85/s | 0 | 0 | 0 | 1.085s |
| Astra easy (promoted) | 184 | 0.88/s | 0 | 0 | 0 | 0.579s |
| Luna medium | 580 | 2.76/s | 23 | 11 | 33 | 0.261s |
| Astra medium (promoted) | 529 | 2.52/s | 22 | 11 | 21 | 0.261s |

The numeric difficulty for the promoted medium chart is `hard` internally and
`Medium` in the menu because the inherited engine has no separate medium id.

The current singer pass was authored against the supplied concept image through
Blender MCP. Each reusable character now has one rounded egg-shaped body rather
than separate legs, a deeper round head, fitted hair, tiny peeking feet, and a
soft blush gradient in the face texture rather than protruding cheek geometry.
The Android-friendly exports are about 13k triangles for raised hands and 12.7k
for joined palms. The standalone menu build explicitly removes the
`CYTOID_FLUTTER_HOST` define during compilation so plugin-export state cannot
disable its local difficulty buttons.

The standalone menu build keeps the rhythm engine's `Game` camera and audio
clock authoritative. `KiirtanGameplayVisualLoader` loads `KiirtanMvp` additively,
puts the visual world on the `KiirtanVisual` layer, renders it behind the note
playfield, and binds `KiirtanWorldDirector` to the gameplay music source. The
Flutter bridge export still uses its documented `CoreHostBootstrap` plus `Game`
scene set and is not changed by this standalone composition.

The source recording stays at its original local path. The checked-in trimmed
clip and package are the prototype runtime copies. Confirm attribution and
distribution rights again before a store release.

## Verification

From the repository root:

```bash
python3 tools/audio/validate_c2_level.py \
  --level engines/unity/Assets/Kiirtaniyas/Levels/hladini_shakti_excerpt/level.json \
  --analysis docs/audio/hladini_shakti_excerpt.analysis.json
~/.unity/bin/unity test engines/unity --mode EditMode --output /tmp/kiirtan-editmode.xml
~/.unity/bin/unity build engines/unity --target Android \
  --execute-method Kiirtaniyas.Editor.KiirtanMvpBuild.BuildAndroidMvpBatch \
  --output-path /tmp/KiirtaniyasMvp.apk --allow-dirty-build
```

The Android smoke build is ARM64 and uses the production identifier
`me.tigerhix.cytoid` for the temporary APK. A connected device is still needed
for install, audio-latency checks, thermal profiling, and tuning the crowd
budget.

## Next implementation slice

1. Review the easy and medium charts by ear and play both on Android.
2. Validate the same composition through a bridge-launched `Game` session after
   the standalone camera and note-play-area review is approved.
3. Replace duplicated foreground singers with reduced-detail or instanced
   variants for stadium-scale backgrounds.
