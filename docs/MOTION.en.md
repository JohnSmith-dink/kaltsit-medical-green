# Local video wallpaper · v1.4.0

`kaltsit-motion` is an optional Plasma wallpaper package. Installing it does not activate it or change the global theme, lockscreen, panel or startup splash.

## Install and select

Build from the release source with `nix build --no-write-lock-file path:.#kaltsit-motion`.
Use a v1.4.0 flake input following the system's pinned nixpkgs:

```nix
# Add to the system flake inputs; a local path to downloaded source also works.
inputs.kaltsit.url = "github:JohnSmith-dink/kaltsit-medical-green/v1.4.0";
inputs.kaltsit.inputs.nixpkgs.follows = "nixpkgs";
```

In a NixOS module receiving `inputs`:

```nix
{ inputs, pkgs, ... }:
let
  motion = inputs.kaltsit.packages.${pkgs.stdenv.hostPlatform.system}.kaltsit-motion.override {
    inherit (pkgs) lib stdenvNoCC kdePackages;
    baseTheme = pkgs.callPackage (inputs.kaltsit + "/package.nix") { };
    # Both optional: select media later in wallpaper settings instead.
    videoFile = /absolute/path/to/balanced.mp4;
    posterFile = /absolute/path/to/poster.jpg;
  };
in { environment.systemPackages = [ motion ]; }
```

Pass inputs to NixOS modules using `specialArgs = { inherit inputs; };`.
The package already supports `.override { videoFile = ...; posterFile = ...; }`.
Passing the system's build arguments and base resource package also keeps Plasma/Qt overlays consistent.

Alternatively, use local `callPackage`:

```nix
{ pkgs, ... }:
let
  source = /absolute/path/to/kaltsit-medical-green;
  baseTheme = pkgs.callPackage (source + "/package.nix") { };
  motion = pkgs.callPackage (source + "/motion.nix") {
    inherit baseTheme;
    # Optional. Omit these to choose a local video in wallpaper settings.
    videoFile = /absolute/path/to/wallpaper.mp4;
    posterFile = /absolute/path/to/poster.jpg;
  };
in {
  environment.systemPackages = [ motion ];
}
```

Allow the `kaltsit-theme` and `kaltsit-motion` unfree package names using your existing Nix configuration policy.
Home Manager can install the extension independently:

```nix
{ inputs, ... }: {
  imports = [ inputs.kaltsit.homeManagerModules.default ];
  programs.kaltsit-theme.motion = {
    enable = true;
    # videoFile = /absolute/path/to/balanced.mp4;
    # posterFile = /absolute/path/to/poster.jpg;
  };
}
```

Pass inputs via Home Manager's `extraSpecialArgs`. `motion.enable` defaults to false; both paths default to null.
It does not require the base theme's `enable`. It reuses the module's `pkgs` and existing `package` option for the base still, only adds resources to `home.packages`, and never writes KDE settings or selects a wallpaper.

The default poster's relative path supports only the Nix package layout. If copying the plugin manually into `~/.local/share`, specify a still in settings. The relative-path implementation is unchanged.

Select **Medical Green · Motion** in Configure Desktop and Wallpaper. The default package contains no video and shows the existing still image until a local video is selected.
If an already-running Plasma process cannot find the newly installed QML dependency, log out and back in.

`videoFile` and `posterFile` are copied into the local Nix store as build inputs. Do not send private media to a public binary cache or include it in shared source.
A path selected directly in wallpaper settings is not copied into the Nix store and must remain available.

## Behavior and recovery

Playback is silent and loops without color grading or overlays. Choose aspect-preserving crop or fit.
The desktop context menu pauses and resumes playback. Pause keeps the current frame; hidden components pause. The `Paused` setting persists across sessions: a right-click pause remains paused after restart.
Missing or invalid video falls back to a still. While playback is allowed, retry every 60 seconds, at most three additional attempts. Pausing blocks reopening media; resuming waits a full interval. Show video only after a new valid frame arrives. Exhaustion is logged and keeps the still; changing the video source resets the budget.
Qt Quick's pure software backend uses the still rather than continuous playback; Qt Quick RHI is required for video rendering.
Battery power pauses by default, with an option to keep playing. A locked-session signal also pauses. Manual pause takes priority and is never cleared by automatic conditions. DPMS and complete window occlusion are not connected.

To disable, choose your original wallpaper plugin and image before removing the addon.
The existing `kaltsit-theme apply/restore` commands do not manage the optional wallpaper selection. Before upgrading or restoring the base theme, return to the original image wallpaper; then follow the [base-theme recovery guide](UPGRADE-RECOVERY.en.md).

## Validation

Accepted development source `7c175b8` ran on NixOS generation 56, Plasma 6.6.6 / Qt 6.11.2, on a 3120×2080 display at 175%.
The user confirmed smooth appearance and working right-click pause/resume. Isolated native checks also covered 1920×1080 / 100%, looping, hidden-state pause, error fallback and recovery.
Release builds keep the same playback logic. Hardware decoding was not conclusively measured; long-term power use and multiple displays remain untested.
See [release evidence](V1.3-RELEASE.md), [acceptance data](v1.3-acceptance.json) and [credits](../CREDITS.md).

## Automatic pause signal research (v1.4)

The pinned nixpkgs revision is `da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36`, with Plasma 6.6.6 / Qt 6.11.2.
On 2026-11-01 an offscreen Qt process with a private HOME, runtime directory and D-Bus observed real KDE QML modules driven by fake services:

| Condition | Source and observation | Decision |
|---|---|---|
| Battery | The powermanagement DataSource `AC Adapter / Plugged in` followed fake `PowerSaveStatusChanged` transitions in both directions; DBusServiceWatcher observed service loss and reconnection | Query the same service's `GetPowerSaveStatus` directly and subscribe to changes, avoiding the engine's fallback to AC when its initial query fails |
| Lock | `org.freedesktop.ScreenSaver`, `/ScreenSaver`: initial `GetActive=false` and both `ActiveChanged(true/false)` reached the real SignalWatcher | Use the initial query and paired notifications, not `canLock` or `AboutToLock` |
| DPMS | No suitable per-screen power notification was found and reproduced; no real virtual output off/on transition was observed | Not connected; neither idle time nor `visible` is treated as DPMS |
| Complete occlusion | Complete coverage across screens, virtual desktops, activities and transparent windows was not verified | Not connected; maximization alone is insufficient |

Battery and lock transitions used **controlled fake D-Bus services**, not physical unplugging or authenticated locking. Qt, DataSource, SignalWatcher and service watchers were real. The daily desktop was untouched. No process polling, daemon or window-tracking service was added for missing conditions.

Sources: [power engine](https://github.com/KDE/plasma5support/blob/v6.6.6/src/dataengines/powermanagement/powermanagementengine.cpp), [lock state implementation](https://github.com/KDE/kscreenlocker/blob/v6.6.6/interface.cpp), [QML signal interface](https://github.com/KDE/plasma-workspace/blob/v6.6.6/components/dbus/dbussignalwatcher.h).
`GetActive` compares `KSldApp::Locked`; lock/unlock emit `ActiveChanged(true/false)` respectively.
Qt Multimedia's `playbackRate` changes playback speed. Reliable decoder frame limiting at normal speed was not established, so no `reduce` policy is offered.

Completion checks: real Qt RHI / Mesa software OpenGL passed 35 behavior checks in private KWin; the pure software renderer passed static fallback. Signals came from private fake services. Checks include same-source file repair, exhaustion of three retries, paused retry suppression, reconnection, and recreating the component with the persisted pause value supplied. Tests shorten the internal interval to 700 ms; production defaults to 60000 ms. Physical unplugging, authenticated locking and DPMS were not tested.

## Prepare a video

The repository distributes no video. Users are responsible for video copyright and usage permission. The standalone [encode-wallpaper.sh](../scripts/encode-wallpaper.sh) is not wrapped into a Nix package; it requires Bash, GNU coreutils and ffmpeg:

```sh
bash scripts/encode-wallpaper.sh /path/to/input.mp4
bash scripts/encode-wallpaper.sh --fps 24 --width 1280 --bitrate 4M /path/to/input.mp4 /path/to/wallpaper.mp4
```

Defaults are silent H.264 / yuv420p / faststart / 30 fps, width at most 1920, preserved aspect ratio without upscaling, even dimensions, and maxrate 6M. Override numeric settings with `--fps`, `--width` and `--bitrate`.
Default output is `<name>-wallpaper.mp4` in the input's real directory. Explicit output must remain in that directory; existing files and symlinks are rejected. Only local file protocols are allowed; no network, audio, subtitle, data tracks or metadata are retained. Handle any partial output from a failed run yourself, then retry with a new filename.
Fake ffmpeg tests check arguments and path boundaries; this script has not undergone real transcoding acceptance. See the [measurement procedure](MOTION-MEASUREMENT.en.md).

CI boundary: the local real-playback probe using `QT_QPA_PLATFORM=offscreen` and software OpenGL timed out in its first phase. The pure software renderer establishes only static fallback. No playback job was added to the existing `weekly.yml`; `ci.yml` is unchanged. Development did not run GitHub Actions; release build CI is checked separately and is not playback validation. Passing private KWin checks does not establish Ubuntu hosted-runner compatibility.

Current release build evidence: [v1.4 release record](V1.4-RELEASE.md).
