# Kal'tsit · Medical Green

**1.1.0-rc.3 — a restrained light desktop theme for NixOS and KDE Plasma 6 / Wayland.**

[中文说明](README.md)

Warm white `#F4F7F2`, white panels, dark green-grey text `#25352D`, and teal accents
`#2E6B57`. A small Plasma style adds fine borders and soft shadows; uncovered
elements use Breeze. Native application controls and the light terminal palette
remain intact. Installation does not activate the theme.

rc.3 removes lock-screen brightness adjustments at the user's request. All
wallpaper overlays are removed, and this theme's password view disables the
brightness, contrast, and saturation transforms. The original JPEG bytes and
native blur, authentication, input, and focus behavior are retained. Lock-screen
controls use dark text on light backgrounds. RC.3 builds and isolated regression
checks passed; deployment and user confirmation on the physical screen are pending.
See [release readiness](docs/RELEASE-READINESS.md).

![Dolphin in a separate Plasma session, 3120×2080 at 175%](previews/actual/dolphin.png)

This is a real application capture from an isolated local Plasma session.
All ten rc.3 preview images have been recaptured. The preview manifest identifies
each capture's version and renderer.
See the [preview notes](previews/README.md) for
desktop, launcher, terminal, notification, and lock-screen test captures.

## Build and install

```sh
nix build --no-write-lock-file path:.#kaltsit-theme
nix profile install path:.#kaltsit-theme
kaltsit-theme status
```

The existing lock file is reused. The complete package is marked `unfree` because
the artwork has separate rights; see [CREDITS.md](CREDITS.md). If Home Manager
already installs the package, update that source instead of installing a second
copy. Install the assets before applying: a running Plasma process must be able
to discover them through its user or system data directories.

RC.3 installs a complete Plasma shell resource layer that participates in shell
package discovery. Build it with the same `pkgs` as the system and rebuild it
when upgrading Plasma: a package pinned to an old flake may shadow the new
system shell. The Home Manager module uses the caller's `pkgs` by default.

```sh
kaltsit-theme apply --dry-run
kaltsit-theme apply
kaltsit-theme status
kaltsit-theme restore
```

An active older version must be restored before applying this version. Repeating
the same version and options keeps the original backup. Changing component
choices or the custom wallpaper also requires `restore` first. Never delete the
backup to bypass a restore conflict.

## Components and custom wallpaper

```sh
kaltsit-theme apply --skip cursor --skip gtk
kaltsit-theme apply --wallpaper /absolute/path/to/wallpaper.png
```

`core` is mandatory. Optional components are `cursor`, `wallpaper`, `lockscreen`,
`gtk`, `ghostty`, and `konsole`; repeat `--skip` to omit several. If a core
configuration file is a symlink, apply refuses before changing anything. A
symlink-managed optional configuration causes that entire component to be
skipped, with a recorded reason. The result is `partially-applied` when components
are skipped, even though applying the remaining components succeeded. `status`
reports `applied`, `skipped`, or `not-applied` for each component and works without
a running Plasma session.

`--dry-run` only reads configuration and session state and reports planned values
and skip reasons. It creates no backup directory, writes no configuration, sends
no refresh notifications, and does not change the desktop. Actual apply checks
the commands needed for the selected components and requires a logged-in Plasma
session. Existing system commands on `PATH` take precedence over packaged
fallbacks.

A custom wallpaper is validated before changes begin and is used for desktop
and lock screen unless the corresponding component is skipped. Images are
center-cropped while preserving aspect ratio (`FillMode=2`). The bundled default
remains frame 707 of the original 4K source; the package contains no full video.

## Home Manager

```nix
{ ... }: {
  imports = [ ./path/to/kaltsit-medical-green/home-manager.nix ];
  programs.kaltsit-theme.enable = true;
}
```

The module uses the caller's `pkgs`; allow the `kaltsit-theme` unfree package or
set `programs.kaltsit-theme.package` to the flake package output. It installs the
theme and Breeze GTK without an activation hook. Stylix and plasma-manager are
not required.

For a declaratively managed Ghostty configuration:

```nix
{
  programs.kaltsit-theme.enable = true;
  programs.kaltsit-theme.ghosttyThemeFile = true;
  programs.ghostty.settings.theme = "Kaltsit Medical Green";
}
```

`ghosttyThemeFile` defaults to `false`. With the module enabled, it installs
`$XDG_CONFIG_HOME/ghostty/themes/Kaltsit Medical Green` without changing the
Ghostty configuration. Use `--skip ghostty` when managing that choice yourself.

## Preservation and recovery

The controller preserves panel placement, pinned applications, desktop icons,
fonts, scaling, cursor size, command-line shell, and shortcuts. It uses KDE configuration tools
and restores only affected settings for applied components. Later unrelated edits
remain intact; conflicting edits to the same keys are reported and kept with the
backup for resolution. Failed application attempts roll back their changes.

State format 3 records component choices and remains compatible with formats 1
and 2. Backups live under
`${XDG_STATE_HOME:-$HOME/.local/state}/kaltsit-theme/active.json`. Restore with the
current tool before downgrading. A missing old Nix path referenced by the
Ghostty backup does not prevent removal of the controller's own configuration
block; restoring configuration does not recover deleted assets.

The cursor keeps its `Kaltsit-Sihengtu` ID and all five sizes (24/32/48/64/96),
animation frames, and hotspots. Existing user-local copies that would shadow the
package are reversibly backed up before linking to the new assets. These sizes
are nearest-neighbour scaling of the original 32px pixel art, not newly drawn
high-resolution artwork. Cursor source: pinned
[kaltsit-cursors commit 7ef139a](https://github.com/JohnSmith-dink/kaltsit-cursors/tree/7ef139a6210fd8eb03d0296b624d71eaa3120589);
original artist: [一球咸鱼](https://space.bilibili.com/3585839);
[artist's video](https://b23.tv/zHvHCpF).

Original code, Plasma SVGs, and folder icons use MIT. Generated QML derived from
KDE keeps its upstream GPL-2.0-or-later license and is outside the MIT scope.
Character and cursor artwork also have separate rights; see
[CREDITS.md](CREDITS.md) and the cursor notices.
SDDM, Plymouth, boot interfaces, and browser-specific skins are outside scope.

## Lock-screen rendering and compatibility in rc.3

RC.1 was too bright, and the user found rc.2's dimming and overlays too dark.
RC.3 removes all wallpaper overlays. When the Fader's `source.pluginName`
identifies this theme's lock-screen plugin, its contrast, saturation, and
intensity factors stay at 1. Native blur remains enabled; other wallpaper
plugins retain KDE's original color transforms. The Complementary palette returns
to dark text on light backgrounds to keep the clock and controls readable against
the original image; wallpaper brightening remains disabled for this theme.

This version adapts Plasma shell QML at build time. Nix generates local QML
changes from matching KDE dependencies and copies unchanged upstream files
byte-for-byte into the build output. The repository does not maintain an
authentication source fork. Exact source matches guard the generated changes; an unexpected
upstream structure stops the build for compatibility review. See the
[validation notes](docs/VALIDATION.md) for details. The generated upstream-derived
QML retains GPL-2.0-or-later notices.

## Validation

```sh
nix develop --command python3 -m unittest discover -s tests -v
nix flake check --no-write-lock-file path:.
```

RC.3's 69 tests, offline Nix build, and `flake check` passed. Resource preflight
checks confirm that missing resources cause no configuration writes, and applying
and restoring with the lock-screen component explicitly skipped also passed.
Both full isolated regression suites passed: RHI at 3120×2080 / 175%, and the
software backend at 1920×1080 / 100%. Ten preview images were recaptured.
Deployment and user confirmation on the physical screen remain pending.
All 68 unit tests passed for rc.2. The palette check
covers every foreground role against normal and alternate backgrounds in each
KDE color group. RC.2's 128 pairs had a minimum contrast of approximately 4.56:1.
The unchanged normal
terminal ANSI colors have a minimum contrast of 5.58:1, and faint colors 4.51:1.

RC.1 passed isolated native KDE checks for apply, repeat apply, restore, failure
rollback, and migration from v1.0 / dev.2. It was then installed as NixOS
generation 52. Real locking, unlocking, and everyday cursor clicks worked, but
the user reported an almost-white password background, so visual acceptance
failed. RC.2 passed isolated RHI and software-rendering checks, restore and
rollback, and the local Nix build; the user then found the result too dark and
requested removal of brightness adjustments. These historical results do not
replace rc.3's remaining physical-screen confirmation.
See [validation notes](docs/VALIDATION.md) for results and component boundaries.

The CI workflow is included with third-party Actions pinned to full commits.
The dev.2 and rc.1 runs passed. The rc.2 and rc.3 local builds passed; rc.3 hosted
checks will run after the branch is pushed. See the
validation notes and repository Actions for version-specific results.
