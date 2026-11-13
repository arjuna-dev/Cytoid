# AGENTS.md - Kiirtaniyas United

> **IMPORTANT: Keep this file up-to-date.** When build paths, integration targets, or the ecosystem layout change, update this document. An outdated AGENTS.md is worse than none.

## Project Overview

**Kiirtaniyas United** is an early-stage kiirtan rhythm game built as a focused fork of Cytoid. The Unity gameplay core lives in `engines/unity/` and handles note rendering, audio, hit detection, scoring, and the storyboard engine. The project keeps this proven rhythm foundation while adding kiirtan songs, authored levels, and a new visual world.

| Item | Value |
|------|-------|
| Product | **Kiirtaniyas United** |
| Source base | Fork of `Cytoid/Cytoid` |
| GitHub fork | `arjuna-dev/Cytoid` |
| Git remotes | `origin` -> fork; `upstream` -> `Cytoid/Cytoid` |
| Unity editor | **6000.0.75f1** (`engines/unity/ProjectSettings/ProjectVersion.txt`) |
| Language | C# |
| Unity project root | `engines/unity/` |
| Visual reference | `reference-images/exec-aa9f4acb-ac7a-4b5d-976e-48ad70ea4b62.png` |
| Current phase | First vertical slice implementation; core gameplay preserved |

### Runtime modes

`GameEmbedMode` (`engines/unity/Assets/Scripts/Host/GameEmbedMode.cs`) selects behavior at compile/runtime:

| Mode | Define / trigger | Behavior |
|------|------------------|----------|
| **Standalone debug** | Default in Editor (no `CYTOID_FLUTTER_HOST`) | Navigation + Game for in-editor Play Mode |
| **Bridge-embedded** | `CYTOID_FLUTTER_HOST` on plugin export builds | `CoreHostBootstrap` + `bridge.play.start` → Game; results via `GameBridge` / host protocol |

### Product direction and non-negotiable visual constraints

- Preserve Cytoid's touch timing, scoring, audio synchronization, and C2 chart format. Do not invent new note semantics for kiirtan gestures.
- Use one close isometric scene and keep it intimate throughout. The singer count should move from one to two, three, and eventually a stadium-scale circle while keeping the foreground intimate and allowing most of the crowd to recede into the background. The progression is visual richness and scale, not a change from intimate to distant.
- Singers always travel clockwise around one central table. This is background choreography, not a player-controlled mechanic and not a special note type.
- Favor raised hands. Joined palms are the alternative pose. Production singers should not hold instruments unless this decision is explicitly revisited.
- Enrich the same courtyard with plants, light, weather, and atmosphere as the music progresses. The visual progression has a heavenly stage, then a space-like cosmic stage, then a trippy cosmic stage with sacred geometry and fractals over a black background. At the very ending, all other characters disappear and the single main character floats alone in cosmic space.
- Create production 3D assets in Blender through Blender MCP and run the presentation as a real-time 3D Unity environment. Generated video is not part of the runtime presentation plan.
- Keep the spiritual framing grounded in collective kiirtan and service. Do not add generic mind-suppression, attachment, ego, or idol-worship mechanics without an explicit design decision.
- The concept sheet in `reference-images/` is a mood board for lighting, palette, and progression. It is not a literal staging or asset specification.

### Current work boundary

This fork now contains the first Kiirtaniyas United vertical slice: Blender-authored source and exports, an audio-driven Unity presentation scene, cute looping singer dance clips, reference-led rounded singer characters, visual stage scripts, measured song analysis, easy and medium C2 charts, a decorated inherited menu, and a built-in level package. Keep future implementation focused on integrating this slice with the inherited gameplay and Flutter host, reviewing charts on Android, and validating performance. Do not add spiritual mechanics or unrelated engine rewrites without an explicit design decision.

### Inherited Cytoid identifiers

The Unity menus, C# namespaces, package identifiers, Flutter plugin names, and bridge classes still use `Cytoid` names. This is expected during the setup phase. Do not perform a broad rename just to make labels match Kiirtaniyas United. Rename an identifier only when a concrete implementation task requires it and all host, Android, iOS, and protocol references can be updated together.

### AI-assisted level authoring north star

Level creation is a first-class future workflow. The target loop is:

1. Analyze each kiirtan recording for BPM, beat grid, onsets, phrase boundaries, and melody cues.
2. Give structured analysis data to an LLM to propose a C2 chart and difficulty variants.
3. Validate the generated chart deterministically for schema, timing, playability, and audio alignment.
4. Inspect the chart in an existing editor, playtest it, and revise it with human approval.

LLMs should work from measured audio data and existing chart tooling rather than inventing millisecond timings by guesswork. The engine should remain generic; spiritual meaning belongs in the authored song, chart, and visual direction rather than hardcoded note behavior.

The first song prototype uses the 3:00 to 6:30 excerpt of `/Users/alejandrocamus/Downloads/Hladini shakti kiirtana.mp3` (3 minutes 30 seconds). This section should be charted from measured beat timings and a tempo map rather than a single assumed BPM, since the recording is expressive and not metronomed.

### Scenes (build order)

| Scene | Path | Role |
|-------|------|------|
| Bootstrapper | `engines/unity/Assets/Scenes/Bootstrapper.unity` | Splash (distribution-specific), loads Navigation |
| Navigation | `engines/unity/Assets/Scenes/Navigation.unity` | Menus, `ScreenManager`, local DB init |
| CoreHostBootstrap | `engines/unity/Assets/Scenes/CoreHostBootstrap.unity` | Minimal Bridge-embedded runtime bootstrap; no Navigation UI |
| Game | `engines/unity/Assets/Scenes/Game.unity` | Gameplay |
| KiirtanMvp | `engines/unity/Assets/Scenes/KiirtanMvp.unity` | First real-time 3D Kiirtaniyas presentation slice; audio-driven stage preview |

Navigation scenes remain for in-editor debugging with Play Mode. **Plugin exports** use **CoreHostBootstrap + Game** only (`CytoidCoreBuild.PluginBuildScenes`).

## Repository Structure

```
Kiirtaniyas-United/
├── engines/
│   └── unity/
│       ├── Assets/             # Unity scenes, scripts, plugins, shaders, resources
│       ├── Packages/           # UPM manifest (UniTask, unity-mcp, ...)
│       ├── ProjectSettings/
│       └── flutter_plugin/     # cytoid_game_core Flutter plugin, examples, artifact tools
├── art/
│   └── blender/                 # Blender source files and authoring work
├── tools/                      # Monorepo-level maintainer scripts
├── docs/                       # Monorepo-level docs
├── reference-images/           # Visual references and mood boards, not final assets
├── .github/workflows/          # GameCI + Flutter plugin artifact packaging
└── README.md                   # Human-oriented project overview
```

### Canonical payload types (host protocol)

Dart models in `engines/unity/flutter_plugin/lib/src/models/` mirror C#:

- `engines/unity/Assets/Scripts/Game/GameLaunchPayload.cs`
- `engines/unity/Assets/Scripts/Game/GameLaunchBridge.cs`
- `engines/unity/Assets/Scripts/Game/GameResultBridge.cs` and its v2 wire payloads

Protocol spec: `docs/host-protocol-v2.md` (v1 doc at `engines/unity/flutter_plugin/example/docs/host-protocol.md` is DEPRECATED; keep `cytoid_flutter/docs/host-protocol.md` in sync).

**JNI / native callback (Android):** Unity C# → `NativeHostMessenger` → `org.cytoid.gamecore.UnityHostCallback.onMessage` (implemented in `engines/unity/flutter_plugin/android/`). Not the legacy `com.example.cytoid_flutter.host.UnityHostCallback` string in older README text.

**Native send failures (Android `sendToUnity` / `returnToFlutterActivity`):** when the reflective `UnitySendMessage` call or the `startActivity` back to the Flutter Activity throws, the failure is NOT surfaced as a synchronous `PlatformException` from `send()`. `send()` returns `Future<void>` and callers have no wait point to convert the exception. Instead, the bridge routes the failure asynchronously via the v2 § Active-Session Runtime Failure contract:

- `activeSessionId == null` → `engine.error` envelope via the EventChannel, `error.code = "runtime_exception"`, message sanitized to `"<ExceptionClassSimpleName>: <first message line>"` (no raw stack trace).
- `activeSessionId != null` → synthesized `session.failed` with `error.code = "runtime_unreachable"` via the T4 primitive. Never both — active-session failures use `session.failed` ONLY; `engine.error` is for non-session failures.

**Host-side `health.check` watchdog (Dart):** `PlaySession._awaitSessionResult` arms a self-scheduling watchdog that sends `health.check` every `pollInterval` (default 10s). First response timeout = 30s, subsequent = 10s. A check is skipped when a non-terminal engine envelope arrived within the last `pollInterval`. On response timeout, the watchdog completes the session completer with `CytoidGameCoreSessionFailedException(code: 'runtime_unreachable')` — the same code the native bridge uses for send-failure synthesis, distinguished by the `message` field. This fills the gap the native synthesis paths don't cover: Unity main loop frozen with the process alive (storyboard death-spiral, GC stall). The C# handler is at `engines/unity/Assets/Scripts/Host/GameBridgeRouter.cs` (`HandleHealthCheck`, returns `health.ok` with `engine` / `generation` / `state` / `activeSessionId`).

**Android Unity Activity lifecycle (warm-resident):** the exclusive Unity Activity (`me.tigerhix.cytoid.CytoidPluginActivity`) is NOT `finish()`-ed on session end. `hideGameSurface()` brings the Flutter Activity to front via `FLAG_ACTIVITY_REORDER_TO_FRONT | FLAG_ACTIVITY_SINGLE_TOP` and leaves the Unity Activity warm-resident in the back stack. This keeps Unity/IL2CPP/GL state alive across the typical play loop (select level → play → result → select next), eliminating the 5–15s cold-start tax on every session.

Activity lifecycle callbacks drive the T3 state machine:
- `onActivityPaused` (Unity Activity) → `runtimeState.onSuspend()` (READY|BUSY → SUSPENDED; single-slot prior state preserved).
- `onActivityResumed` → `runtimeState.onResume()` (SUSPENDED → prior state).
- `onActivityDestroyed` → if `activeSessionId != null`, T4's `synthesizeRuntimeFailure(SURFACE_LOST, sessionId)` fires (emits `session.failed` with `error.code = "runtime_surface_lost"`, transitions to FAILED); otherwise `runtimeState.reset()` returns to UNAVAILABLE (caller must `startRuntime()` again).

A `@VisibleForTesting unityActivityInstanceCount` counter tracks live Unity Activity instances. In the warm-resident policy this counter MUST stay at 0 or 1 across arbitrary session cycles; a value > 1 indicates Activity accumulation (memory leak). The memory regression test runs 10 sequential session cycles via low-level primitives and asserts the counter never exceeds 1.

The Unity Activity source lives in the AAR and is NOT editable from this repo. Lifecycle integration is exclusively via `Application.ActivityLifecycleCallbacks` registered in `CytoidGameCoreBridge.attachActivity`.

---

## Build & Debug

Plugin builds: **Cytoid → Build Android/iOS Plugin Artifacts** (`engines/unity/Assets/Scripts/Editor/CytoidCoreBuild.cs`). Storyboard vendor check: **Cytoid → Log Storyboard Effects Backend**.

### Package identifiers

| Build | Android `applicationId` |
|-------|-------------------------|
| Production (ProjectSettings) | `me.tigerhix.cytoid` |
| Flutter Unity library export | `com.example.cytoid_flutter.unity` |
| Flutter example app | `com.example.cytoid_flutter` |
| Flutter plugin namespace | `org.cytoid.gamecore` |

### Flutter plugin artifacts (primary)

Editor: **Cytoid → Build Android/iOS Plugin Artifacts** (export + package in one step).

Android batchmode:

```bash
UNITY="/Applications/Unity/Hub/Editor/6000.0.75f1/Unity.app/Contents/MacOS/Unity"
PROJECT="/path/to/KIIRTAN_CYTOID/engines/unity"

"$UNITY" -batchmode \
  -projectPath "$PROJECT" \
  -executeMethod CytoidCoreBuild.ExportAndroidLibraryForFlutter \
  -logFile "$PROJECT/flutter_plugin/.cytoid_game_core/build/unity-android.log"
```

Exports to `engines/unity/flutter_plugin/.cytoid_game_core/exports/android/unityLibrary`, then runs `engines/unity/flutter_plugin/tool/build_unity_aar.sh` → `engines/unity/flutter_plugin/.cytoid_game_core/artifacts/unity/android/cytoid-unity-core.aar` (+ dependency AARs).

Re-package only (after manual export edits): `cd engines/unity/flutter_plugin && ./tool/build_unity_aar.sh`

IL2CPP ARM64 export typically takes **5–15+ minutes** on a clean machine.

Run example:

```bash
cd engines/unity/flutter_plugin/example && flutter pub get && flutter run
```

Without artifacts, the plugin uses a **mock engine** (host protocol still works).

Optional download: `CYTOID_GAME_CORE_ARTIFACT_BASE_URL` + `./tool/setup_unity_artifacts.sh`.

CI: `.github/workflows/flutter-plugin-artifacts.yml` is manual-only
(`workflow_dispatch`). It uses GameCI `unity-builder@v4` for Android AAR
export/package and, when `build_ios` is enabled, iOS UnityLibrary export. iOS
`UnityFramework.xcframework` packaging runs afterward on macOS/Xcode from the
exported Xcode project. The workflow uploads GitHub Actions artifacts only; it
does not create release PRs, tags, GitHub Releases, or dart.dev publications.

### cytoid_flutter (full app)

Documented in sibling repo: `cytoid_flutter/docs/unity-android-export.md`, `scripts/export_unity_android.sh`.

Requires Unity export at `cytoid_flutter/android/unityLibrary/` (set `Cytoid.FlutterUnityLibraryRelativePath` in Unity EditorPrefs if batch export uses the plugin default path).

```bash
cd cytoid_flutter
export UNITY_PATH="/Applications/Unity/Hub/Editor/6000.0.75f1/Unity.app/Contents/MacOS/Unity"
./scripts/export_unity_android.sh
flutter run
```

### iOS Bridge-embedded

> **iOS Simulator runs mock-only because the current Unity artifact is device-only. Real-device testing is required for Unity verification.**

- Batch or **Cytoid → Build iOS Plugin Artifacts**: `CytoidCoreBuild.ExportIOSLibraryForFlutter`
  exports to `engines/unity/flutter_plugin/.cytoid_game_core/exports/ios/UnityLibrary`, then runs
  `engines/unity/flutter_plugin/tool/build_unity_ios_framework.sh` (requires macOS + Xcode) to write
  `engines/unity/flutter_plugin/.cytoid_game_core/artifacts/unity/ios/UnityFramework.framework` and
  `UnityFramework.xcframework`; Swift Package Manager uses the `.xcframework`.
- CI can call `CytoidCoreBuild.ExportIOSLibraryForFlutterWithoutPackaging` to
  export the UnityLibrary Xcode project on GameCI/Linux and package it later on
  macOS.
- Re-package only: `cd engines/unity/flutter_plugin && ./tool/build_unity_ios_framework.sh`
- The current Unity iOS export is device-only. Simulator builds need a simulator
  slice in `UnityFramework.xcframework`, or no mounted Unity artifact so the
  plugin falls back to the mock runtime.
- Swift test suite: the pure-logic iOS tests run without `FlutterFramework`
  or `UnityFramework` via `./tool/run_swift_tests_sandboxed.sh` (isolated
  SwiftPM sandbox with a stub `Flutter` module). Tests asserting on real
  Flutter semantics (`ShowGameSurfaceAtomicityTests`) require an Xcode build
  with full dependencies.
- The Flutter plugin example iOS app is Swift Package Manager only; do not
  re-add `Podfile`, `Podfile.lock`, Pods xcconfig includes, or manual
  UnityFramework link/embed entries to `Runner.xcodeproj`.
- `cytoid_flutter`: see `docs/unity-ios-export.md` and `scripts/export_unity_ios.sh`

### Batch entry points

| Method | Purpose |
|--------|---------|
| `CytoidCoreBuild.ExportAndroidLibraryForFlutter` | Export Gradle library + AAR artifacts |
| `CytoidCoreBuild.ExportIOSLibraryForFlutter` | Export Xcode project + UnityFramework.xcframework (device) |
| `CytoidCoreBuild.ExportIOSLibraryForFlutterWithoutPackaging` | Export iOS Xcode project only; CI packages on macOS |

---

## Conventions for Agents

### Language & style

- **English** for code, comments, commit messages, and user-visible debug strings unless a feature explicitly requires localization.
- Match existing patterns in `engines/unity/Assets/Scripts/` (UniTask, Newtonsoft JSON, namespace layout).
- **Minimize scope** — prefer focused changes; do not refactor unrelated Unity or Flutter code.

### Licensing & assets

- Optional paid packages under **`engines/unity/Assets/Vendor/<Package>/`** (gitignored), installed via maintainer zip (`engines/unity/flutter_plugin/tool/install_vendor_from_archive.sh`). Example: `engines/unity/Assets/Vendor/StoryboardFilters/`. Open-source clones use fallbacks in `engines/unity/Assets/Shaders/Storyboard/`. See `docs/vendor.md`.
- Some other commercial plugins and art are **not** in this fork and may only exist in legacy `Cytoid-private` sources. Do not commit licensed third-party assets or secrets.
- `Builds/`, `Library/`, `engines/unity/flutter_plugin/.cytoid_game_core/exports/`, and artifact binaries are **local-only** (gitignored).

### CytoidGameCore protocol changes

If you change envelope types or payloads:

1. Update C# (`engines/unity/Assets/Scripts/Host/`, `GameLaunchPayload`, `GameResultBridge`, …).
2. Update Dart models in `engines/unity/flutter_plugin/lib/`.
3. Update `docs/host-protocol-v2.md` and keep `cytoid_flutter/docs/host-protocol.md` in sync if the contract changed.

### Testing on device

- Prefer **plugin artifact builds** and `engines/unity/flutter_plugin/example` for Flutter ↔ Unity messaging (`bridge.play.start`, `game.play.result`, `game.ready`, `bridge.ping`).
- Android logcat: `adb logcat -s Unity ActivityManager`

### Unity MCP

`engines/unity/Packages/com.coplaydev.unity-mcp` is present for editor automation; optional for agents with Unity Editor access.

### Unity CLI

The Unity CLI is installed at `~/.unity/bin/unity` on the primary development machine (currently version `1.0.0-beta.6`). The pinned Unity `6000.0.75f1` Silicon editor is installed at `/Applications/Unity/Hub/Editor/6000.0.75f1/Unity.app/Contents/MacOS/Unity` with Android Build Support, Android SDK and NDK Tools, and OpenJDK. Unity Hub may default to a newer Unity 6 release, so do not allow a newer editor to upgrade project files without an explicit decision. Agents working on Unity tasks should use the CLI for project inspection, diagnostics, editor status, builds, tests, and opening the project before resorting to manual editor actions.

- Resolve the executable with `command -v unity` or `zsh -lic 'whence -p unity'`; if it is not on `PATH`, invoke `~/.unity/bin/unity`.
- Prefer non-interactive, project-scoped commands and machine-readable output where useful: `unity --non-interactive status`, `unity doctor --ci`, `unity build <project>`, and `unity test <project>`. Check each command's `--help` for current options.
- Use `unity open engines/unity` when an editor session is needed, and `unity status --project-path engines/unity` to inspect connected editors.
- Do not install or uninstall editors, change Unity license or account settings, or modify project files or assets solely as a side effect of diagnostics. Keep commands scoped to this project unless the user asks otherwise.
- For plugin exports, install Android Build Support with SDK, NDK, and OpenJDK, plus iOS Build Support when targeting iOS, in the same pinned Unity editor installation. Web Build Support alone is not sufficient.

### Blender and Blender MCP

Blender 4.3.2 is installed at `/Applications/Blender.app/Contents/MacOS/Blender`. The community `blender-mcp` server is launched with `uvx --python 3.11 blender-mcp`, and its Blender add-on is installed under `~/Library/Application Support/Blender/4.3/scripts/addons/blender_mcp.py`. Blender MCP telemetry is disabled for this project setup. Open Blender, enable `Interface: MCP for Blender` in Preferences, and start the MCP server from the `BlenderMCP` sidebar tab before asset-authoring work. Keep `.blend` source files under `art/blender/`; export runtime assets into `engines/unity/Assets/Kiirtaniyas/Art/` through the Blender MCP authoring workflow.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05 | Unity 6 (6000.0.75f1) core fork | IL2CPP / mobile toolchain modernization |
| 2026-05 | Engine-agnostic host protocol | Flutter shell; future Godot adapter |
| 2026-05 | `cytoid_game_core` plugin + versioned AAR artifacts | Example app and CI can avoid committing `unityLibrary` trees |
| 2026-05 | Dual export targets (plugin `.cytoid_game_core/exports` vs `cytoid_flutter/android/unityLibrary`) | Plugin packaging vs full-app Gradle embed |
| 2026-05 | Tier = single `bridge.play.start` session + `tierPlay` launch/result | Flutter orchestrates multi-stage runs; core keeps `tierHpMods` only |
| 2026-05 | No Unity disk persistence (LiteDB removed) | Settings/records/scores live in Flutter; core uses in-memory `LocalPlayerSettings`, `LevelRecord`, `GameLaunchSettings` |
| 2026-05 | Lunar Console removed; `game.log` forwarding | Bridge-embedded receives Unity logs; Graphy retained for in-engine profiler overlay |
| 2026-05 | Cytoid top-level menu = plugin builds only | Flat `Cytoid/…` items; no Core Build submenu; exports use `PluginBuildScenes` + `CYTOID_FLUTTER_HOST` |
| 2026-06 | Host-side `health.check` watchdog in `PlaySession` | Detects Unity main-loop freeze with process alive — the gap the native bridge synthesis paths don't cover. Reuses `runtime_unreachable`; provenance in `message`. C# handler: `GameBridgeRouter.HandleHealthCheck` |
| 2026-07 | `CytoidCoreBuild` uses `EditorApplication.update` + explicit `EditorApplication.Exit(0)`; invocation MUST NOT pass `-quit` | Unity 6 batchmode + `-quit` exits the instant executeMethod returns, so `update` callbacks never fire and any async work is silently dropped. Empirically verified: `Thread.Sleep` deadlocks (compiler shares the main thread); `EditorApplication.Step()` is a no-op inside executeMethod (doesn't pump compilation, doesn't advance wall clock); `wantsToQuit` vetoes are ignored under `-quit`. CI uses game-ci/unity-builder `manualExit: true` (added in PR game-ci/unity-builder#574 specifically for this pattern). |
| 2026-07 | Swift test suite runs in `tool/run_swift_tests_sandboxed.sh` (isolated SwiftPM sandbox with stub `Flutter` module) | The iOS plugin's pure-logic tests must run without the `FlutterFramework` SPM package or `UnityFramework` binary target — neither is available locally. Harness realizes the "isolated SwiftPM sandbox" convention already documented in 5 source files. Excludes `ShowGameSurfaceAtomicityTests` (asserts on real Flutter semantics) and `CytoidGameCorePlugin.swift` (UIKit + Flutter entry point). |
| 2026-07 | Unity no longer owns community-level installation, profile persistence, first-launch state, or remote asset caching | Flutter supplies a complete settings snapshot plus a local VFS root for every bridge session. Unity retains only session runtime state and a minimal built-in/local loader for standalone Editor debugging. |
| 2026-09 | Cytoid fork personalized as Kiirtaniyas United | Preserve the inherited rhythm engine while documenting the kiirtan, isometric visual progression, AI-assisted charting direction, and setup-only work boundary. |
| 2026-09 | Real-time Blender-to-Unity presentation | Create all production 3D assets through Blender MCP, assemble and animate the intimate isometric gathering in Unity, and use heavenly, space-like cosmic, sacred-geometry cosmic, and single-MC ending stages. Do not use video as the runtime presentation path. |
| 2026-09 | First song prototype excerpt | Use 3:00 to 6:30 from `Hladini shakti kiirtana.mp3`; author its chart from measured beats and a tempo map instead of assuming a fixed BPM. |
| 2026-09 | First vertical slice implementation | Blender MCP exports an expanded courtyard and two cute singer poses with a looping Lalita Marmika dance; Unity drives five intimate visual stages from the excerpt AudioSource; measured easy and medium charts are packaged for built-in loading. |
| 2026-09 | Inherited menu reuse | The standalone Android smoke build can include Bootstrapper, Navigation, and Game; the Navigation scene keeps the Cytoid flow while presenting the first Kiirtaniyas song card and maps the inherited `hard` chart id to the visible Medium button. |
| 2026-09 | Candidate chart promotion | Promote the Astra medium-thinking easy and medium candidates for the first runtime package after deterministic comparison with Luna max-thinking candidates; retain all four candidate folders for human listening and Android playtest review. |
| 2026-09 | Reference-led character pass | Submit the supplied concept image to Astra high through Blender MCP; use rounded egg-shaped bodies, deep round heads, texture-only soft blush, fitted hair, and tiny feet while preserving raised-hands/joined-palms poses and the looping dance. |
| 2026-09 | Standalone menu build isolation | `KiirtanMvpBuild` removes `CYTOID_FLUTTER_HOST` while building the standalone Android MVP/menu APK, then restores the editor define symbols, so the inherited Navigation controller remains active after plugin exports. |
| 2026-09 | Standalone gameplay visual composition | `KiirtanGameplayVisualLoader` loads `KiirtanMvp` additively over the standalone inherited `Game` scene, isolates it on the `KiirtanVisual` layer, and binds the world director to the gameplay music source; bridge exports remain on `CoreHostBootstrap` + `Game` until separately validated. |

Append new rows when architecture or default paths change.

---

## Key File Index

| Topic | Location |
|-------|----------|
| Build menu / batchmode | `engines/unity/Assets/Scripts/Editor/CytoidCoreBuild.cs`; MVP APK: `engines/unity/Assets/Editor/Kiirtaniyas/KiirtanMvpBuild.cs` |
| CI plugin artifacts | `.github/workflows/flutter-plugin-artifacts.yml` |
| Vendor asset install | `engines/unity/flutter_plugin/tool/install_vendor_from_archive.sh`, `docs/vendor.md` |
| Game bridge | `engines/unity/Assets/Scripts/Host/GameBridge.cs` |
| Wire envelope (C#) | `engines/unity/Assets/Scripts/Host/CytoidGameCoreEnvelope.cs` |
| Game log forwarding | `engines/unity/Assets/Scripts/Host/GameLogBridge.cs` |
| Embed mode | `engines/unity/Assets/Scripts/Host/GameEmbedMode.cs` |
| Visual reference | `reference-images/exec-aa9f4acb-ac7a-4b5d-976e-48ad70ea4b62.png` |
| Kiirtaniyas visual runtime | `engines/unity/Assets/Scripts/Kiirtaniyas/Visual/` |
| Standalone gameplay visual composition | `engines/unity/Assets/Scripts/Kiirtaniyas/Visual/KiirtanGameplayVisualLoader.cs` |
| Kiirtaniyas MVP scene builder | `engines/unity/Assets/Editor/Kiirtaniyas/KiirtanMvpSceneBuilder.cs` |
| First song analysis and tooling | `docs/audio/hladini_shakti_excerpt.md`; `tools/audio/` |
| MVP vertical slice handoff | `docs/kiirtaniyas-mvp.md` |
| Native outbound (game → bridge) | `engines/unity/Assets/Scripts/Host/NativeBridgeMessenger.cs` |
| Flutter plugin (Kotlin) | `engines/unity/flutter_plugin/android/src/main/kotlin/org/cytoid/gamecore/` |
| Flutter plugin (iOS Swift / SPM) | `engines/unity/flutter_plugin/ios/cytoid_game_core/` |
| Swift test sandbox harness | `engines/unity/flutter_plugin/tool/run_swift_tests_sandboxed.sh` |
| Flutter Dart API | `engines/unity/flutter_plugin/lib/src/cytoid_game_core_client.dart` |
| Protocol doc | `docs/host-protocol-v2.md` (v1 doc at engines/unity/flutter_plugin/example/docs/host-protocol.md is DEPRECATED) |
| Legacy architecture notes | `engines/unity/flutter_plugin/example/docs/old-architecture/` |
