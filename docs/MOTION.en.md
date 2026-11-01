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
