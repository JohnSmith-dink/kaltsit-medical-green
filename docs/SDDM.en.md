# Login screen (SDDM, experimental)

`kaltsit-sddm` is a separate static Qt 6 login theme, disabled by default. It does not change the desktop, lockscreen, Home Manager, authentication policy or daily restoration records. It uses the existing still and generates colors from the existing scheme at build time.
See the [initial design](SDDM-DESIGN.en.md) for pinned dependencies and fallback boundaries. The v2 layout below is an unpublished UI revision; the package version remains 1.3.0.

## v2 layout and keyboard controls

- The wallpaper retains its original brightness and aspect-preserving crop, with no full-screen overlay, large card or blur. Centered time and date appear above, using the greeter font and minute precision; the clock uses existing dark text with a thin white outline.
- The lower-center login area places the username above a 280×48 logical-pixel password field and a separate circular arrow. Username, inputs, errors and bottom actions have separate 96%-opaque white backplates. Text and borders remain opaque; no text is smaller than 14 logical pixels.
- Activate the username even with a single user to open the list. “Other…” replaces the username line with an input; an empty model shows it directly. An unlisted remembered username is prefilled, and the adjacent list button returns to listed accounts. Changing accounts clears the password and old error.
- Initial focus goes to the password, or to the username when unknown. Tab/Shift+Tab traverse visible controls; arrow keys move in a list, Return selects, and Esc closes it and restores trigger focus. Return used to select a list item does not submit credentials.
- Session selection and the read-only keyboard layout sit at bottom left; shutdown and reboot text buttons sit at bottom right. An empty session list explains why login is disabled. Submission prevents duplicate actions and retains the original session index and power-capability checks.
- Errors occupy reserved space below the password and wrap when needed. A roughly 600 ms error border is separate from the focus border. Submission and failure clear the password; failure restores password focus. Passwords are not logged or written to files. Authentication behavior, CLI, Nix interfaces and the lockscreen are unchanged.

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

It loads the real greeter with `--test-mode --theme` and ends that process after six seconds, then sends actual key and mouse events through the matching `qmltestrunner` with mock SDDM models. Each run has 13 behavior checks covering zero/one/multiple users, manual usernames, sessions, Tab/Return/Esc, duplicate submissions, password clearing, errors and power calls. Layouts are checked at 1280×800/100%, 1920×1080/100% and 3120×2080/175%.

Resolution-specific output directories contain `single-user.png`, `error.png`, `multi-user-menu.png`, `long-username.png` and `results.json`. These are native Qt renders with mocks, not authentication evidence. At 175%, Qt rounds the logical capture size and produces a raw 3120×2081 PNG. The report records requested layout, logical size and captured pixels separately; it does not crop or resize away that difference.

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

## Evidence from the initial implementation

On 2026-11-01 (America/Los_Angeles), runtime resources came from `4e9363d` and the module from `e50d903`, using the nixpkgs revision recorded in the design.

- The real SDDM 0.21.0 / Qt 6.11.2 greeter loaded with private HOME, D-Bus and offscreen software rendering, without embedded fallback; it also loaded in private KWin Wayland. Five mock-model UI checks passed; those checks did not authenticate.
- `nixos-rebuild build-vm --flake path:.#sddm-test` succeeded. The VM used NixOS 26.05, 2 cores / 2048 MiB, 1280×800, an X11 greeter and xterm session. Its read-only test closure image shared no host HOME. Control access was forwarded only to host loopback and used a disposable test SSH key.
- A real wrong-password submission in the VM produced an error, cleared the password and restored focus. The test password then passed PAM and entered xterm; logging out returned to the themed greeter. User and session menus opened, with only one entry each; keyboard layout displayed `us`.
- Breaking only a temporary theme copy inside the VM produced `DeliberatelyMissingTestType is not a type` and `Fallback to embedded theme` in the journal, with the embedded SDDM UI visible. Authentication was not repeated in that fallback UI; this does not prove login under arbitrary failures.
- **Full power-cycle validation did not pass**: both the VM reboot and shutdown buttons entered system shutdown, then stalled around `Failed unmounting /nix/store`. Reboot did not produce a new boot ID, and shutdown did not exit within 90 seconds. Those test VM processes were terminated. The cause remains undiagnosed; neither complete reboot/shutdown nor physical-machine behavior is claimed.

The [login screen](../previews/sddm/login.png) and [wrong-password screen](../previews/sddm/wrong-password.png) retain original QEMU screenshot bytes. The [manifest](../previews/manifest.json) records per-entry VM environment, source commits and SHA-256. Old screenshots are unchanged; no concept image substitutes for validation.
No host SDDM theme was activated, host service restarted or host configuration deployed. Physical activation remains a future decision; VM login results are not complete physical acceptance.

## v2 validation evidence

On 2026-11-02 (America/Los_Angeles), the runtime UI came from `6afcb9ecf12112d4cbd438ea3a471fcda15f02f9`. The package version remains 1.3.0; Nix packaging, modules and authentication configuration are unchanged.

- The real SDDM 0.21.0 / Qt 6.11.2 test-mode loaded with private HOME, D-Bus and offscreen software rendering. Mock-model checks passed 13 behaviors at each of the three sizes/scales, 39 in total, sending actual Tab, Shift+Tab, Return, Esc, arrow-key and mouse events. Zero/one/multiple users and long usernames are covered; multiple-user lists were not tested with physical-machine accounts.
- Native Qt captures were inspected at all three sizes for clock outlines, lists, long usernames, errors and bottom controls; no overlap or overflow was observed. Compositing the 96%-opaque white backplate over the darkest underlay gives approximate contrast ratios of 11.85, 4.85, 5.95 and 5.74:1 for body text, placeholder text, errors and focus borders respectively. Calculations use the existing palette without changing color values.
- This round reused the previously built NixOS 26.05 test VM with a fresh temporary disk; `build-vm` was not rerun. Only the newly built theme resources were copied into a temporary directory **inside the guest**. Main.qml, Palette.js and background SHA-256 values were compared before loading them via a guest-only configuration. No host HOME share or host service operation was used.
- In the 1280×800, 100%, X11/xterm test environment, PAM rejected an incorrect password. The correct fixture password authenticated and entered xterm; logout returned to the v2 greeter. Deliberately breaking a temporary guest QML copy produced `Fallback to embedded theme` and the embedded login UI. Authentication was not repeated in the fallback UI.
- Power buttons were checked only against the mock backend; full VM shutdown/reboot was not retested. The initial incomplete power-cycle checks remain unresolved. The harness stopped its own VM process at the end; that is not evidence of a successful shutdown action.

The [v2 login screen](../previews/sddm/login-v2.png) and [v2 wrong-password screen](../previews/sddm/login-v2-error.png) are original 1280×800 QEMU captures from that VM, without postprocessing. Only these two entries and their SHA-256 values were appended to the manifest; earlier captures and entries remain intact. Physical hardware, a real high-DPI greeter, multiple displays and full power cycles remain outside this round's validation conclusions.

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
