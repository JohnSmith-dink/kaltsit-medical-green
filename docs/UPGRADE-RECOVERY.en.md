# Upgrade, recovery and removal

[中文](UPGRADE-RECOVERY.md) · [Back to README](../README.en.md)

## Upgrade order

1. Run `kaltsit-theme status` in your current KDE session and note the applied version and components.
2. Run `kaltsit-theme restore` with the currently installed tool. Resolve any reported conflicts and retry if it returns `restore-incomplete`; do not delete the backup to bypass the check.
3. Update, build and install the package. Home Manager users should update their configured source and rebuild normally, without installing a second copy through `nix profile`.
4. Run `kaltsit-theme apply --dry-run`, apply with your chosen `--skip` / `--wallpaper` options, then check `status`.

First use needs no restore. Repeating apply with the same version and options keeps the original backup. Restore before changing options, wallpaper or version.
The development branch still reports `1.1.0`: `upgrade_available` compares version strings, not source commits. Restore and apply explicitly when testing the D1 development package too.

## Plasma upgrades and version diagnostics

Build the complete Plasma shell resource layer with **the same `pkgs` as the system**. The Home Manager module does this by default; the standalone flake's locked KDE may differ from your system.
Rebuild the theme when upgrading Plasma, then log out and back in so the running session uses the new packages.

`status` includes `lockscreen_resources`:

| Field | Meaning |
|---|---|
| `built_for.plasma_desktop` / `plasma_workspace` | Nix-supplied build versions from the installed `lockscreen-rendering.json`. |
| `running.version` | Nix store package version of the Plasma process owning the current session bus name. Reads its PID and `/proc`; never starts another plasmashell. |
| `match` | `true` when both build versions equal the running version, `false` when they differ, or `"unknown"` when metadata, session, tools or recognizable process provenance are unavailable. |

`true` means matching version numbers, not guaranteed compatibility across builds, patches or displays. `false` adds a rebuild hint; it neither changes settings nor blocks commands.
Offline status still reads configuration and recovery records. Old packages without the new metadata report unknown instead of guessing.

## Restore and conflicts

```sh
kaltsit-theme restore
kaltsit-theme status
```

Only applied components are restored. Unrelated later edits survive. A theme-owned key changed by the user is kept and reported as a conflict.
Use the output to set conflicting keys back to their theme-applied values, then retry restore. To retain a personal value, note it separately and reselect it through System Settings after recovery; retrying with the conflict still present reports it again. Do not overwrite whole configuration files or edit active.json directly.
Unmodified files are restored with their original bytes where possible; later-edited files are restored per key. GTK restores only theme-owned keys, retaining exported fonts and other settings.
State formats 1, 2 and 3 remain readable. Restore with the current tool before downgrading; older tools reject unfamiliar records.

The recovery record is `${XDG_STATE_HOME:-$HOME/.local/state}/kaltsit-theme/active.json`.
It contains personal configuration, and its directory may also contain cursor backups. Keep it private and do not remove it before recovery.
Original cursor directories or links are restored. Restoring configuration does not download old Nix resources that have already been garbage-collected.

## If the graphical interface is unusable

Log into a TTY (usually Ctrl+Alt+F2) as **the same user** and connect to the existing user session bus:

```sh
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
kaltsit-theme status
kaltsit-theme restore
```

This is a recovery procedure, not a real lockscreen failure drill passed in this round. Do not run theme switching with sudo.
If you normally customize `XDG_CONFIG_HOME`, `XDG_DATA_HOME` or `XDG_STATE_HOME`, use the same values in the TTY.
If Plasma or its bus has exited, restore may not complete live refresh. Keep the errors and backups, recover a usable session, then retry.
If a NixOS or Plasma package upgrade caused the problem, select the previous system generation in the boot menu. This does not undo user configuration; inspect and restore it once the session works.

## Remove

Complete restore before removing resources. Home Manager users should disable `programs.kaltsit-theme.enable`, remove related Ghostty declarations, then rebuild normally.
For profile installations, identify the entry with `nix profile list`, then use `nix profile remove <entry-name>`.
Do not remove unrelated sources or the whole profile. Deleting the recovery record is not an uninstall procedure.
