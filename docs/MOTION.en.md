# Local video wallpaper · v1.3.0

`kaltsit-motion` is an optional Plasma wallpaper package. Installing it does not activate it or change the global theme, lockscreen, panel or startup splash.

## Install and select

Build from the release source with `nix build --no-write-lock-file path:.#kaltsit-motion`.
For installation, use the same `pkgs` as the running Plasma/Qt system. For example:

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
Home Manager users may put the same derivation in `home.packages` instead; the existing theme module API is unchanged.
Select **Medical Green · Motion** in Configure Desktop and Wallpaper. The default package contains no video and shows the existing still image until a local video is selected.
If an already-running Plasma process cannot find the newly installed QML dependency, log out and back in.

`videoFile` and `posterFile` are copied into the local Nix store as build inputs. Do not send private media to a public binary cache or include it in shared source.
A path selected directly in wallpaper settings is not copied into the Nix store and must remain available.

## Behavior and recovery

Playback is silent and loops without color grading or overlays. Choose aspect-preserving crop or fit.
The desktop context menu pauses and resumes playback. Pause keeps the current frame; hidden components pause.
Missing or invalid video falls back to a still and recovers when a valid source is supplied.
Qt Quick's pure software backend uses the still rather than continuous playback; Qt Quick RHI is required for video rendering.
Fullscreen-window occlusion, locking and battery state are not automatic pause triggers in this version.

To disable, choose your original wallpaper plugin and image before removing the addon.
The existing `kaltsit-theme apply/restore` commands do not manage the optional wallpaper selection. Before upgrading or restoring the base theme, return to the original image wallpaper; then follow the [base-theme recovery guide](UPGRADE-RECOVERY.en.md).

## Validation

Accepted development source `7c175b8` ran on NixOS generation 56, Plasma 6.6.6 / Qt 6.11.2, on a 3120×2080 display at 175%.
The user confirmed smooth appearance and working right-click pause/resume. Isolated native checks also covered 1920×1080 / 100%, looping, hidden-state pause, error fallback and recovery.
Release builds keep the same playback logic. Hardware decoding was not conclusively measured; long-term power use and multiple displays remain untested.
See [release evidence](V1.3-RELEASE.md), [acceptance data](v1.3-acceptance.json) and [credits](../CREDITS.md).

## Automatic pause signal research (Unreleased)

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
