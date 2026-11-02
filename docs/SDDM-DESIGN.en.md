# Experimental SDDM theme design

This is the initial v1.4 development design, recorded while package versions remained 1.3.0. See the [v1.4 release record](V1.4-RELEASE.md) for final scope. `docs/ROADMAP-v1.2.md` does not exist. `V1.2-DEVELOPMENT.md` only postpones SDDM. This round adds an independent, disabled-by-default system extension without expanding the base package or Home Manager's runtime responsibilities.

## Inspected dependencies and format

Actual evaluation of pinned nixpkgs `da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36` returned SDDM 0.21.0, Qt base 6.11.2 and qtdeclarative 6.11.2.
Inspected sources:

- nixpkgs [`pkgs/applications/display-managers/sddm/unwrapped.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/pkgs/applications/display-managers/sddm/unwrapped.nix): version, `BUILD_WITH_QT6`, qtbase/qtdeclarative dependencies and four patches.
- [`default.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/pkgs/applications/display-managers/sddm/default.nix): wraps the greeter; `extraPackages` joins its build environment for Qt's QML import wrapping.
- SDDM 0.21.0 [`ThemeMetadata.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/common/ThemeMetadata.cpp): INI `metadata.desktop`, group `[SddmGreeterTheme]`, `MainScript=Main.qml`, `ConfigFile=theme.conf`, `QtVersion=6`. Omitting QtVersion defaults to Qt 5, so 6 must be explicit.

Deliver `Main.qml`, `metadata.desktop`, `theme.conf`, generated palette and the existing static JPEG. Use only QtQuick, QtQuick.Layouts, QtQuick.Controls.Basic and the greeter-provided `sddm/userModel/sessionModel/keyboard` context. The pinned SDDM depends on qtdeclarative providing these Qt modules. No Kirigami, Plasma or third-party QML dependency is planned. Actual import loading remains unverified at the design stage.

## NixOS integration

Based on pinned [`nixos/modules/services/display-managers/sddm.nix`](https://github.com/NixOS/nixpkgs/blob/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36/nixos/modules/services/display-managers/sddm.nix):

- `services.displayManager.sddm.theme` is a string, default empty; `extraPackages` lists additional Qt plugins/QML libraries.
- ThemeDir is `/run/current-system/sw/share/sddm/themes`; enabling SDDM links `/share/sddm`.
- Install the theme at `$out/share/sddm/themes/KaltsitMedicalGreen`; `environment.systemPackages` makes it discoverable.
- `programs.kaltsit-sddm.enable` defaults to false. Explicit enabling installs the separate `kaltsit-sddm` package and sets the theme with `lib.mkOverride 900` (above Plasma defaults, below explicit user settings). Explicit user themes win. Do not enable SDDM itself or change PAM, autologin or unrelated settings.
- Existing greeter dependencies cover planned imports; no extraPackages are expected. Add a dependency only if loading demonstrates a specific missing module. Reuse the caller's `pkgs`, with no second nixpkgs.

## Visual and interaction scope

Use the existing static wallpaper and derive colors at build time from `share/color-schemes/KaltsitMedicalGreen.colors`; add or change no palette values. Use aspect-preserving crop and an opaque login panel.
Provide only user selection, username entry, password, error text, session selection, keyboard-layout display, shutdown and reboot. No video, animation, avatar upload or extra language switcher. Keep Chinese `qsTr` strings without a new translation pipeline.
Error text must reach 4.5:1 contrast, control boundaries 3:1, with visible keyboard focus. Send passwords only to SDDM's login API, never logs or files; clear and refocus after failure. SDDM remains responsible for authentication and session startup.
Retain mixed-asset unfree handling and existing attribution/source statements. SDDM runtime resources are independent; existing base-package document collection may change its hash.

## Risks and recovery

[`GreeterApp.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/greeter/GreeterApp.cpp) handles QQuickView load errors by switching to `qrc:/theme/Main.qml`, logging `Fallback to embedded theme`. Add no custom fallback logic. This covers QML loading errors, not display-server, Qt-plugin, daemon or PAM failures.
`--test-mode` loads the UI; it cannot establish real PAM authentication or session startup. Without a daemon, power capabilities default to false ([`GreeterProxy.cpp`](https://github.com/sddm/sddm/blob/v0.21.0/src/greeter/GreeterProxy.cpp)).

For a future first physical-machine activation, retain a previous boot generation and known-good declarative configuration and confirm TTY access. Run `sudo nixos-rebuild build --flake /path/to/system#host`, then `sudo nixos-rebuild boot --flake /path/to/system#host`, and inspect on the next boot. Do not use `switch` for first activation.
On failure choose the previous NixOS generation in the boot menu. Menu names depend on the bootloader; physical recovery is unverified. Alternatively try Ctrl+Alt+F3, log in to a TTY, then run:

```sh
sudo nixos-rebuild boot --rollback
sudo reboot
```

Or set `programs.kaltsit-sddm.enable` back to false, restore any previously explicit theme setting, then build, boot and reboot as above. The command source is pinned `nixos-rebuild-ng/src/nixos_rebuild/__init__.py` accepting BOOT with rollback, and `nix.py` using `nix-env --rollback` on the system profile before the selected generation's boot-install action. Only source semantics were inspected; these host recovery commands were not executed. Recovery cannot depend on missing generations or garbage-collected closures.

## Validation sequence

1. Build with `nix build --no-write-lock-file path:.#kaltsit-sddm`. Build `kdePackages.sddm` from the same lock and run its `bin/sddm-greeter-qt6 --test-mode --theme /nix/store/<theme-package>/share/sddm/themes/KaltsitMedicalGreen`. Execution must use private HOME/XDG directories, D-Bus and offscreen or a private display server. The pinned greeter's `--help` confirmed these two arguments.
2. Define `nixosConfigurations.sddm-test` in a private test flake. Enable SDDM/theme and fictional accounts only there; import no host configuration, HOME share or real credentials. From a temporary directory run `nixos-rebuild build-vm --flake /absolute/path/to/test-flake#sddm-test`, then `./result/bin/run-sddm-test-vm`. Complete configuration and execution evidence will be supplied in validation; no VM has been built at the design stage.
3. In the VM, check wrong/correct passwords, session startup, logout back to the greeter, and SDDM's fallback for a deliberately broken theme. Test power buttons only in the VM. Label screenshots as test-mode or VM, place them in `previews/sddm/`, and append manifest entries only.

## Unconfirmed

At the design stage the new theme, VM authentication/power actions/broken-theme fallback, physical machine and recovery path are unverified. Multi-display behavior, special input methods and assistive authentication are also unverified. Screenshots will not be presented as proof of those checks. If VM execution is blocked, retain unverified status and reproduction steps without activating the host theme.

Implementation correction: `services/desktop-managers/plasma6.nix` sets `mkDefault "breeze"` at priority 1000. Another equal-priority default would conflict, so the theme uses 900, retaining explicit user settings at priority 100. Evaluation checks cover both Plasma defaults and user overrides. No service enablement or authentication behavior was added.
