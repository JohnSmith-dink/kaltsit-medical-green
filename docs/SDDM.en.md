# Login screen (SDDM, experimental)

`kaltsit-sddm` is a separate static Qt 6 login theme, disabled by default. It does not change the desktop, lockscreen, Home Manager, authentication policy or daily restoration records. It uses the existing still and generates colors from the existing scheme at build time.
See the [design](SDDM-DESIGN.en.md) for pinned dependencies and fallback boundaries.

## Install and enable

Reference the local development branch in the system flake, with `inputs.kaltsit.inputs.nixpkgs.follows = "nixpkgs"`, and pass inputs to modules via `specialArgs`. Use a local path for unpublished code; the public 1.3.0 release does not contain this work.

```nix
{ inputs, ... }: {
  imports = [ inputs.kaltsit.nixosModules.default ];
  programs.kaltsit-sddm.enable = true;
  # Your system configuration must enable SDDM separately; this module does not.
}
```

Add `kaltsit-sddm` to your existing `nixpkgs.config.allowUnfreePredicate`, retaining rules for other packages. The independent package includes existing character artwork and is not an all-free asset package. [Attribution](../CREDITS.md) and license statements are unchanged. The module uses the system's `pkgs.callPackage` and requires Qt 6 SDDM. Pinned SDDM already includes QtQuick, Controls.Basic and Layouts; no additional `extraPackages` are required.

Importing the module or only adding the package to `environment.systemPackages` does not select the theme. Only setting the option to true installs resources and sets a theme name, still without enabling the SDDM service.
The theme default uses priority 900, overriding Plasma's `mkDefault "breeze"` (1000) while explicit user `services.displayManager.sddm.theme = "…"` (100) wins. Remove an old explicit value or select `KaltsitMedicalGreen` yourself; the module never forces it.

For a future first physical-machine activation, retain known-good configuration and a previous generation, complete VM checks below, then configure the option and run:

```sh
sudo nixos-rebuild build --flake /path/to/system#host
sudo nixos-rebuild boot --flake /path/to/system#host
# Reboot when convenient; activate on the next boot, not with switch initially.
```

These are future operator instructions. This round did not deploy a host configuration: no host switch, boot, test or login-service restart was performed.

## Disable and recover

Set `programs.kaltsit-sddm.enable = false`, restore any previous explicit theme setting, then build, boot and inspect after reboot. Remove any separately installed theme package from its original package list if desired. Disabling the module does not rewrite other user SDDM settings.
If the UI fails, select a previous boot generation, or try Ctrl+Alt+F3 to log in to a TTY and run `sudo nixos-rebuild boot --rollback` followed by `sudo reboot`. See [recovery design](SDDM-DESIGN.en.md#risks-and-recovery) for command sources, retained-generation requirements and unverified physical recovery boundaries.
SDDM's embedded fallback handles QML load errors, not arbitrary display-server, plugin or authentication failures. This theme adds no automatic switching script.

## Repeatable isolated validation

Build the theme and use `kdePackages.sddm` and `kdePackages.qtdeclarative` from the same lock for the test tools. The script below creates private HOME/XDG directories, D-Bus and offscreen rendering without accessing the daily session:

```sh
nix build --no-write-lock-file path:.#kaltsit-sddm
python3 tests/run-sddm-native.py "$(realpath result)" \
  --greeter /path/to/matching/sddm-greeter-qt6 \
  --qml /path/to/matching/qml --output /tmp/kaltsit-sddm-native-result
```

It loads the real greeter with `--test-mode --theme`, ends that process after six seconds, then checks focus, password masking/clearing, errors and power capabilities with mock SDDM models. `ui-mock.png` is explicitly native Qt rendering with mocks, not a real login screenshot or proof of authentication.

[tests/sddm-vm.nix](../tests/sddm-vm.nix) is **test-only; never import it into a physical-machine configuration**. It uses 2 cores / 2048 MiB, 1280×800, static wallpaper and X11 greeter. An xterm session isolates SDDM testing; it is not Plasma desktop acceptance. Account `tester` has the public disposable password `wallpaper-test`. There is no host HOME sharing, real credential or host configuration import. A separate read-only Nix store image contains the test closure; default shares and external network access are disabled.

Create this flake in a fresh temporary directory, replacing the source path:

```nix
{
  inputs.theme = { type = "path"; path = "/absolute/path/to/kaltsit-medical-green"; };
  inputs.nixpkgs.follows = "theme/nixpkgs";
  outputs = { theme, nixpkgs, ... }: {
    nixosConfigurations.sddm-test = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [ (theme + "/tests/sddm-vm.nix") ];
    };
  };
}
```

Run only in that temporary directory:

```sh
nixos-rebuild build-vm --flake path:.#sddm-test
./result/bin/run-sddm-test-vm
```

Try an incorrect password, then the fixture password. Run `exit` in xterm to return to the greeter. Check shutdown/reboot buttons only inside the VM.
For broken-theme fallback, copy the theme to a temporary directory **inside the VM**, replace Main.qml with invalid QML, point a temporary guest SDDM configuration at it, and restart the guest display-manager. Check `Fallback to embedded theme` and usable login controls, then remove the guest override. Do not do this on the host.

## Evidence from this round

On 2026-11-01 (America/Los_Angeles), runtime resources came from `4e9363d` and the module from `e50d903`, using the nixpkgs revision recorded in the design.

- The real SDDM 0.21.0 / Qt 6.11.2 greeter loaded with private HOME, D-Bus and offscreen software rendering, without embedded fallback; it also loaded in private KWin Wayland. Five mock-model UI checks passed; those checks did not authenticate.
- `nixos-rebuild build-vm --flake path:.#sddm-test` succeeded. The VM used NixOS 26.05, 2 cores / 2048 MiB, 1280×800, an X11 greeter and xterm session. Its read-only test closure image shared no host HOME. Control access was forwarded only to host loopback and used a disposable test SSH key.
- A real wrong-password submission in the VM produced an error, cleared the password and restored focus. The test password then passed PAM and entered xterm; logging out returned to the themed greeter. User and session menus opened, with only one entry each; keyboard layout displayed `us`.
- Breaking only a temporary theme copy inside the VM produced `DeliberatelyMissingTestType is not a type` and `Fallback to embedded theme` in the journal, with the embedded SDDM UI visible. Authentication was not repeated in that fallback UI; this does not prove login under arbitrary failures.
- **Full power-cycle validation did not pass**: both the VM reboot and shutdown buttons entered system shutdown, then stalled around `Failed unmounting /nix/store`. Reboot did not produce a new boot ID, and shutdown did not exit within 90 seconds. Those test VM processes were terminated. The cause remains undiagnosed; neither complete reboot/shutdown nor physical-machine behavior is claimed.

The [login screen](../previews/sddm/login.png) and [wrong-password screen](../previews/sddm/wrong-password.png) retain original QEMU screenshot bytes. The [manifest](../previews/manifest.json) records per-entry VM environment, source commits and SHA-256. Old screenshots are unchanged; no concept image substitutes for validation.
No host SDDM theme was activated, host service restarted or host configuration deployed. Physical activation remains a future decision; VM login results are not complete physical acceptance.

## Checklist (blank for a new environment)

| Check | Result | Environment / evidence |
|---|---|---|
| Theme loads without implicit fallback | | |
| User selection, username/password focus | | |
| Wrong-password error and clearing | | |
| Correct-password session startup | | |
| Logout back to greeter | | |
| Session selection and keyboard-layout display | | |
| VM shutdown and reboot buttons | | |
| VM broken-theme fallback | | |
| Physical first boot and TTY recovery | | |

## Known limitations

This is an experimental Qt 6 login theme. Physical hardware, boot-menu rollback, TTY recovery, multiple displays, special input methods and assistive authentication are unverified. The system needs a font supporting Chinese; the module does not change user font configuration.
Keyboard layout may appear as unknown in isolated Wayland test-mode; do not interpret it as a physical keyboard layout. SDDM/PAM controls actual authentication. There is no custom fingerprint, smart-card or multi-factor prompt interaction, and no claim of support for those environments.
