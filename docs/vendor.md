# Vendor Assets

`engines/unity/Assets/Vendor/` is intentionally gitignored. It may contain paid or otherwise
non-redistributable Unity packages used by maintainer builds.

The storyboard vendor bundle is expected at:

```text
engines/unity/Assets/Vendor/StoryboardFilters/
```

Maintainer CI can install it from a private zip before Unity import:

```sh
export CYTOID_VENDOR_ARCHIVE=https://example.com/private/storyboard-filters.zip
export CYTOID_VENDOR_ARCHIVE_SHA256=<sha256>
engines/unity/flutter_plugin/tool/install_vendor_from_archive.sh
```

Accepted zip layouts:

```text
Assets/Vendor/StoryboardFilters/...
Vendor/StoryboardFilters/...
StoryboardFilters/...
```

If no archive is configured, builds continue with the in-repo fallback storyboard
effects in `engines/unity/Assets/Shaders/Storyboard/` and `engines/unity/Assets/Scripts/Storyboard/PostProcess/`.
Do not commit `engines/unity/Assets/Vendor/` contents or generated Unity export artifacts.

## Native Audio

The Exceed7 Native Audio package is a separate licensed Unity Asset Store package and
the repository's `engines/unity/Assets/Native Audio/` directory is intentionally
gitignored. The project therefore compiles and runs with the Unity audio backend by
default, including when a payload requests native audio.

To enable the native low-latency SFX backend on Android or iOS, import the purchased
Native Audio package into `Assets/Native Audio/` and add `CYTOID_NATIVE_AUDIO` to the
Unity Scripting Define Symbols for that build target. Do not add the symbol before the
package is imported. The native implementation is kept behind that symbol so editor
imports and standalone development do not require the licensed package.
