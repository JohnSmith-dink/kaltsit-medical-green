# Login screen (SDDM, experimental)

`kaltsit-sddm` is a separate static Qt 6 login theme, disabled by default. It does not change the desktop, lockscreen, Home Manager, authentication policy or daily restoration records. It uses the existing still and generates colors from the existing scheme at build time.
See the [initial design](SDDM-DESIGN.en.md) for pinned dependencies and fallback boundaries. The v5 layout below is an unpublished UI revision; the package version remains 1.3.0.

## v5 layout and keyboard controls

- The wallpaper retains its original brightness and aspect-preserving crop. Clock, date and login panel occupy the left column at approximately x=64…384 logical pixels. The center has no login controls and there is no full-screen overlay.
- Time starts at (64,64), using 72px Light weight; the date uses 18px Normal weight. Both inherit the greeter system font and use existing dark text without outlines. Actual background sampling and contrast results appear below.
- The login area retains v3's 320px width, 16px padding and spacing, and normal center at roughly 55% of screen height. Its container draws no background, rounded frame, border or shadow; there is no blur. Usernames and footer text use existing white with the dark body color at alpha 0.85 for glyph outlines. Clock and date are unchanged.
- The avatar remains a drawn 48px green circle with a 22px white initial; the username is 18px. A single-user row is focusable but opens no menu and offers no “Other account” entry. Multiple users retain the existing inline list and “Other…” entry. An empty model or unlisted remembered account shows the username input; the latter is prefilled.
- The password row remains 44px high with an 8px radius and embedded 36px green arrow. Password and manual-username inputs use their own white surface at alpha 0.94, retaining dark text and placeholders. The 14px error row retains the existing red Negative color with a thin white outline at alpha 0.90; it takes no space when empty. The error border still lasts approximately 600 ms. Submission and failure clear the password; failure restores password focus. Changing accounts clears the password and old error.
- Session, keyboard layout, shutdown and reboot retain their original footer row. Ghost controls are normally transparent and retain their own white alpha-0.90 surface and border on hover/focus. Keyboard layout is focusable but remains read-only; no switching action is added. Long session names are elided and appear in full in the list. Both expanded lists retain their own white alpha-0.90 background, dark text and green selection. No separator existed and none was added.
- Tab follows avatar row → password → login → session → keyboard → shutdown → reboot; Shift+Tab reverses the order. Manual username editing stays in the avatar row; unavailable/hidden controls are skipped. Initial focus still goes to password or username according to whether an account is known.
- Tab/Shift+Tab traverse available controls. Arrow keys move through lists, Return selects, and Esc closes and restores trigger focus without leaking Return into login. User lists expand down and session lists up; only one is open at a time. Height is capped with scrolling, keeping lists inside the panel and clear of the clock. Empty session models explain why login is disabled; submission prevents duplicate actions.
- Package version, authentication policy, CLI, Nix interfaces and the lockscreen are unchanged. Passwords are not logged or written to files.

Outlines use only [QtQuick Text.Outline](https://doc.qt.io/qt-6.11/qml-qtquick-text.html#style-prop), with no new Qt module or font. White comes from the existing Selection foreground; this scheme's Complementary foreground is dark, not white. Normal, error and multiple-user previews, together with raw and outlined contrast values, appear in the v5 evidence below.

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

It loads the real greeter with `--test-mode --theme` and ends that process after six seconds, then sends actual key and mouse events through the matching `qmltestrunner` with mock SDDM models. Each run has 15 behavior checks covering zero/one/multiple users, manual usernames, sessions, Tab/Return/Esc, duplicate submissions, password clearing, errors and power calls. Layouts are checked at 1280×800/100%, 1920×1080/100% and 3120×2080/175%.

The output root contains `results.json`. Resolution subdirectories contain native PNGs for a single user, errors, multiple-user lists, long usernames, session lists, empty user models, avatar/keyboard focus and a background-only frame, plus per-region `contrast.json`. These are native Qt renders with mocks, not authentication evidence. At 175%, Qt rounds the logical capture size and produces a raw 3120×2081 PNG. The report records requested layout, logical size and captured pixels separately; it does not crop or resize away that difference.

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

## v3 validation and wallpaper sampling

On 2026-11-02 (America/Los_Angeles), runtime UI came from `5d80b1b858fdae23a797178dd6238e6181a65219`. Real greeter test-mode loaded successfully. Mock-model QtTest passed 14 behaviors at each of three sizes, 42 in total, including actual key events, left-column bounds, list directions and collapsing/expanding errors.

An independently rendered Qt background-only frame was sampled using actual control coordinates, without averaging colors. Clock and date logical regions are `(64,64,320,88)` and `(64,160,320,24)` respectively (x, y, width, height). Each panel state records darkest/lightest pixels, luminance, source-image mapping and minimum contrast for each foreground. Warm white at alpha 0.86 is composited first; inputs add pure white at alpha 0.9.

| Size / scale | Clock | Date | Username | Password placeholder | Error row | Conservative error-color minimum over panel | Conservative focus-border minimum |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1280×800 / 100% | 8.28 | 8.53 | 9.91 | 5.14 | 4.79 | 4.68 | 4.51 |
| 1920×1080 / 100% | 9.53 | 7.89 | 9.32 | 5.11 | 4.69 | 4.59 | 4.42 |
| 3120×2080 / 175% | 11.15 | 10.91 | 9.81 | 5.14 | 4.79 | 4.68 | 4.52 |

Values are contrast ratios (:1); the clock needs no backplate. The worst whole-panel sample is the 1920×1080 expanded user list: physical region `(64,500)…(384,836)`, darkest source pixel `#21261f` (luminance 0.018085), lightest `#9ba988` (0.371221). The darkest pixel becomes `#d6dad4` after compositing, giving Negative text 4.585709:1. These are sampled/calculated values, not additions to the theme palette. Per-run `contrast.json` contains the remaining regions; unit tests also check a larger combined expansion/error envelope.

The existing NixOS 26.05 test VM runner was reused with a fresh temporary disk; build-vm was not rerun. New theme resources were copied to a guest temporary directory, SHA-256 checked and loaded only inside the guest. A real incorrect password was rejected, the fixture password passed PAM into xterm, and logout returned to v3. A locked guest-only account, `preview2`, provided a real multiple-user model for the expanded-list capture. Only `tester` authenticated; `preview2` login was not tested. Deliberately breaking guest temporary QML produced embedded fallback; authentication was not repeated in that UI.

The [v3 login](../previews/sddm/login-v3.png), [v3 error](../previews/sddm/login-v3-error.png) and [v3 multiple-user list](../previews/sddm/login-v3-multiuser.png) are original 1280×800 QEMU PNGs from the VM. Three manifest entries were appended without overwriting old captures. The first VM script hit the guest service start-rate limit after rapid restarts; resetting that counter only in the guest test harness allowed the complete rerun to pass.

No host deployment, service operation or daily wallpaper change occurred. Full power cycles were not retested; the initial failure record still applies. The 175% run remains mock-model offscreen validation, retaining Qt's extra raw image row from size rounding. Fonts follow the runtime environment, with Light glyph availability depending on installed fonts; no font files were added.

## v5 transparent login area: validation and contrast

On 2026-11-02 (America/Los_Angeles), runtime source was `9af3ef2d0d834ba8a1badf892973684fe60599de`. Real SDDM 0.21.0 / Qt 6.11.2 test-mode loaded with private HOME, D-Bus and offscreen software rendering. All 15 mock-model QtTest behaviors passed at each of three sizes, 45 in total. A new unavailable/hidden-control check and actual key events cover the read-only focus stops, reverse Tab, Return and Esc. Every matching sampled region retains its v3 coordinates; empty container margins match the background-only frame pixel for pixel at all three sizes.

Normal white text uses a dark alpha-0.85 outline; red errors use a white alpha-0.90 outline; input surfaces use white at alpha 0.94. Outlines follow glyphs without restoring a panel background. Raw and outlined results remain separate; [W3C G18](https://www.w3.org/WAI/WCAG22/Techniques/general/G18) describes a local outline as a contrasting backdrop. The table contains minimum ratios (:1) calculated from sampled real Qt background frames, colors and alpha across six layout states. Text requires 4.5 and focus requires 3. Native normal, error, list and focused captures were also inspected: outlines were visible and no text overlap was observed. This is not a claim that every antialiased edge pixel meets the threshold.

| Target | 1280×800 / 100% | 1920×1080 / 100% | 3120×2080 / 175% |
|---|---:|---:|---:|
| Clock | 8.275 | 9.534 | 11.152 |
| Date | 8.528 | 7.888 | 10.913 |
| Username / outline | 8.070 | 9.131 | 8.525 |
| Input text | 11.611 | 11.611 | 11.633 |
| Placeholder | 4.751 | 4.751 | 4.760 |
| Error / outline | 5.540 | 5.440 | 5.494 |
| Session / outline | 9.999 | 11.444 | 10.725 |
| Keyboard / outline | 9.515 | 11.100 | 10.129 |
| Shutdown / outline | 8.946 | 10.736 | 9.807 |
| Reboot / outline | 8.525 | 10.437 | 9.515 |
| Minimum focus border | 5.234 | 5.187 | 5.292 |

**Without outlines, the following regions still fail** and are not reported as passing. These minima across six states are all below 4.5:1; the rendered outlines provide the contrasting backdrop around the glyphs.

| Region without outline | 1280×800 / 100% | 1920×1080 / 100% | 3120×2080 / 175% |
|---|---:|---:|---:|
| Username | 1.003 | 1.666 | 1.240 |
| Error row | 1.006 | 1.001 | 1.000 |
| Footer | 1.249 | 3.190 | 1.964 |

Sampling includes every distinct RGB in each whole control rectangle, not an average. The normal username region is `(144,y,224,48)`; password is `(80,y+64,288,44)`; error is `(80,y+124,288,20)`; footer is `(80,y+124,288,32)`, moving down 36 when an error appears. The three layouts use y=362, 516 and 575.714286 logical pixels respectively. Expanded-list positions are recorded separately for each state. Clock `(64,64,320,88)` and date `(64,160,320,24)` remain unchanged.

Pixel bounds use floor(logical coordinate×scale) on left/top and ceil on right/bottom, retaining floating-point layout values; the 1280 error box is therefore `(80,486)…(368,507)`. The source is 3840×2160: let f=max(target width/3840,target height/2160), with offset `((3840f−target width)/2,(2160f−target height)/2)`. Source coordinates are `(screen pixel coordinate+offset)/f`. Each `contrast.json` region records logical, physical and source-image bounds, darkest/lightest RGB and luminance, their contrast and the region minimum. Raw extrema in normal/error states follow:

| Size / region | Darkest RGB (luminance) | Lightest RGB (luminance) | Raw contrast: darkest / lightest / region minimum |
|---|---|---|---|
| 1280×800 / 100% / username | `#576743` (0.121320) | `#eef6eb` (0.900868) | 6.129 / 1.104 / 1.104 |
| 1280×800 / 100% / error row | `#474843` (0.063796) | `#dae2d3` (0.740013) | 1.422 / 4.883 / 1.006 |
| 1280×800 / 100% / normal footer | `#474843` (0.063796) | `#dbe3d4` (0.747517) | 9.227 / 1.317 / 1.317 |
| 1280×800 / 100% / error footer | `#30332a` (0.031632) | `#dae3d2` (0.744967) | 12.863 / 1.321 / 1.321 |
| 1920×1080 / 100% / username | `#333831` (0.037539) | `#889873` (0.289285) | 11.995 / 3.095 / 3.095 |
| 1920×1080 / 100% / error row | `#35342f` (0.034181) | `#606b5d` (0.137925) | 1.922 / 1.162 / 1.001 |
| 1920×1080 / 100% / normal footer | `#35342f` (0.034181) | `#606b5d` (0.137925) | 12.473 / 5.587 / 5.587 |
| 1920×1080 / 100% / error footer | `#37372f` (0.037498) | `#70756f` (0.173150) | 12.000 / 4.705 / 4.705 |
| 3120×2080 / 175% / username | `#536241` (0.109560) | `#c9d4c3` (0.634446) | 6.581 / 1.534 / 1.534 |
| 3120×2080 / 175% / error row | `#454641` (0.060272) | `#a9b69c` (0.442912) | 1.467 / 3.047 / 1.000 |
| 3120×2080 / 175% / normal footer | `#454641` (0.060272) | `#a9b69c` (0.442912) | 9.522 / 2.130 / 2.130 |
| 3120×2080 / 175% / error footer | `#494a45` (0.067437) | `#a9b4a3` (0.437219) | 8.941 / 2.155 / 2.155 |

Unit tests also cover pure black/white underlays: white text against its dark outline reaches at least 8.070:1, red against its light outline 5.200:1, and input placeholders 4.637:1. Those extreme cases and actual screenshot-background samples are recorded separately. All theme colors come from the existing palette.

The original NixOS 26.05 VM runner was reused with a fresh temporary disk; build-vm was not rerun. Only guest temporary resources were replaced, SHA-256 checked and loaded inside the guest. In the 1280×800, 100%, X11/xterm environment, PAM rejected an incorrect password; the fixture password entered xterm, and logout returned to v5. A temporary locked guest account, `preview2`, provided the multiple-user list; only `tester` authenticated. A deliberately broken temporary guest QML copy triggered embedded fallback; authentication was not repeated in that UI.

The new [normal login](../previews/sddm/login-v5.png), [wrong-password error](../previews/sddm/login-v5-error.png) and [multiple-user list](../previews/sddm/login-v5-multiuser.png) are original 1280×800 QEMU PNGs from that VM, without postprocessing. Only three entries and their SHA-256 values were appended; all 17 earlier entries and images remain intact. The light avatar row in the multiple-user capture is hover feedback; the list owns its light background, while the container remains fully transparent.

A real high-DPI greeter, multiple monitors and physical activation remain unverified; 175% evidence comes from mock-model offscreen rendering. Full shutdown/reboot was not retested and the earlier failure record remains. No host configuration or host SDDM was changed; the harness only terminated its own VM process at the end. One rerun was interrupted by a signal (unit/native checks exited 143; flake exited 1); logs were retained, then sequential reruns passed. Interrupted checks are not counted as passes.

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
