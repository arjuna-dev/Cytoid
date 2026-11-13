# Blender MVP

`kiirtaniyas_mvp.blend` contains the original `Kiirtaniyas_MVP` scene. The source preserves separate stonework, flowers, cloth, face details, and body-part groups for editing. `mvp_preview.png` is a rendered inspection image, not a runtime background.

All geometry was authored for this project through Blender MCP using `build_mvp.py`. No downloaded third-party models or textures are included. These original assets are distributed under the repository's GPL-3.0 license.

## Runtime exports

The three FBX files in `engines/unity/Assets/Kiirtaniyas/Art/Models/` use meters and ground-centered origins. The FBX exporter converts Blender Z-up to Y-up. Characters face Blender -Y before conversion. Confirm the facing direction against clockwise tangents in Unity when instantiating them.

| Model | Meshes | Triangles | Purpose |
|---|---:|---:|---|
| Courtyard | 13 | 76,956 | 14.6 m garden apron around 9.8 m paving, table, plants, trees, benches and lamps |
| SingerRaised | 15 | 9,616 | Round-cheeked saffron MC with raised hands and dance clip |
| SingerJoined | 15 | 8,616 | Round-cheeked teal singer with joined palms and dance clip |

Meshes are combined by material within transform groups during export. Original editable objects remain in the Blender source. Runtime materials retain the `KU_` prefix. FBX includes base colors; Unity's renderer determines the final lighting and shader appearance. The source's lamp material uses emission, which should be restored on its Unity material if the importer does not preserve it.

The singers use named Body, Head, Arm_L, Arm_R, Leg_L and Leg_R groups, prefixed with the singer name. A Blender-authored 36-frame loop at 30 fps adds gentle lateral leaning, head sway, alternating small steps and raised-arm sway. This is a stylized lalita marmika interpretation for review, not a humanoid motion-capture rig. Root travel remains owned by Unity's clockwise orbit component. Joined palms stay together throughout the loop.

`KiirtanSingerImporter` imports only these two FBX files as looping Legacy clips. `KiirtanDancePlayer` starts the imported Animation below an actor root and supports small phase offsets between singers. The animation is baked into the FBX, so the Blender source remains authoritative for the dance. For large crowds, use reduced-detail meshes or GPU instancing rather than duplicating these foreground models without a budget.

`characters_preview.png` shows the updated cheeks, compact proportions, smiling closed eyes, rounded tunics and a side-lean pose. `mvp_preview.png` shows the enlarged garden perimeter. These are Blender look-development previews; Unity lighting will differ.

## Authoring and verification

In Blender MCP, load the script using `runpy.run_path(...)`, then call `setup`, `courtyard`, `singer('SingerRaised')`, `singer('SingerJoined', True)`, `presentation`, and `export` in that order. `setup` refuses to overwrite an existing MVP scene. For edits to the existing scene, reuse only the relevant functions and re-export deliberately.

The preview camera is `Intimate_Isometric`. `ClockwiseOrbit_Guide` has a 2.1 m radius; clockwise means decreasing Z rotation viewed from above in Blender. The lights `Golden_Key`, `Heavenly_Rim`, `Soft_Fill`, and `Table_Warmth` establish the source look. Unity owns stage transitions, changing light colors, crowd progression, cosmic imagery, and the final floating MC.

All three exported files were re-imported into a temporary Blender scene to verify geometry, dimensions, and mesh counts. Courtyard geometry bounds are X/Y -7.3 to 7.3 m and Z -0.41 to 3.7 m. Singers are about 1.89 m tall. The exported raised singer's body rotation changes from zero to approximately 9 degrees between frames 1 and 10, verifying that the dance survives FBX export. Unity import, final shader rendering, and device profiling remain integration checks.
