# Login screen (SDDM, experimental)

`kaltsit-sddm` is a separate static Qt 6 login theme, disabled by default. It does not change the desktop, lockscreen, Home Manager, authentication policy or daily restoration records. It uses the existing still and generates colors from the existing scheme at build time.
See the [initial design](SDDM-DESIGN.en.md) for pinned dependencies and fallback boundaries. Version 1.4.0 publishes the finalized v6 layout below. Historical checks retain their original source/version identities; see the [v1.4 release record](V1.4-RELEASE.md).

## v6 typography, optical alignment and keyboard controls

- The wallpaper retains its original brightness and aspect-preserving crop. The login container is fully transparent, with no panel surface, frame, shadow, blur or full-screen overlay. All colors still come from the existing palette.
- If Qt finds local `OPPO Sans 4.0`, the theme uses it; otherwise it retains the greeter's system font. Time uses 72px, 400 Regular, tabular figures and -0.5px letter spacing; the date uses 18px, 400. Both remain dark and unoutlined. No font binary or network download is added.
- Alignment uses visible glyph edges, not only text boxes: the usual shared edge is E=72px, with clock ink at y=71.75px and date ink at y=152.25px. TextMetrics receives the same family, weight, numeral features and render type as the text and adjusts the side bearings dynamically. Narrow layouts use E=max(24,floor(width×0.075)); column width is capped at 288px.
- The login area normally begins at about 45.1% of screen height, with bottom clearance. The avatar is a 48px green circle with a 22px/500 white initial; username text is 18px/500. The password field is 288px wide, 42px high with an 8px radius and 33px arrow. Password and manual-username fields retain the existing warm-white View background, now opaque, with 15px/400 input text.
- Usernames and footer text retain dark glyph outlines at alpha 0.85. Errors retain the existing red Negative color and white alpha-0.90 outline at 14px/400; the design reference's new red or white error text is not adopted. The error row has an 8px gap and takes no space when empty. Brief error borders, password clearing on submission/failure and refocusing remain unchanged.
- The footer is 32px high with a 10px gap: session and read-only keyboard layout form the left group, shutdown and reboot align right, with at least 12px between groups. Text is 14px, with 400 labels and 500 values/buttons. Only the session value elides; labels, keyboard layout and power text do not shrink. The session list shows full names. Hover uses warm white at alpha 0.16; focus uses an opaque white line and an opaque dark outer edge. Resting controls have no surface. Control boxes may hang slightly outside the optical edge while text aligns.
- Both inline lists retain their own white alpha-0.90 surface, dark text and green selection. User lists expand down, sessions up, mutually exclusively; height limits, scrolling and focus return remain unchanged.
- Tab still follows avatar row → password → login → session → keyboard → shutdown → reboot; Shift+Tab reverses it. The single-user avatar and keyboard layout remain focusable without new actions. Multiple users retain “Other…”; empty models/unlisted remembered accounts use manual input. Hidden or unavailable items are skipped, list Return does not leak into login, and Esc restores trigger focus.
- Accounts, session indices, authentication, no-session blocking, duplicate-submit protection, password clearing and power-capability checks are preserved. This UI revision does not change the CLI, Home Manager or lockscreen. The sole new module option is the optional local font path below.

Outlines still use [QtQuick Text.Outline](https://doc.qt.io/qt-6.11/qml-qtquick-text.html#style-prop) without additional Qt modules. [Browser design references](design/sddm-v6-mockups/README.en.md) are stored separately from actual Qt/VM evidence below; mockups are not login screenshots.

## Install and enable

Place the 1.5.0 candidate source beside the system flake in `./kaltsit-medical-green-1.5.0`. Set `inputs.kaltsit.url = "path:./kaltsit-medical-green-1.5.0"` and `inputs.kaltsit.inputs.nixpkgs.follows = "nixpkgs"`. Pass the inputs through `specialArgs`.

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

### Optional local font

`programs.kaltsit-sddm.fontFile` has type `nullOr path` and defaults to `null`. Only when the theme is enabled and the path is non-null does it add a local font package to `fonts.packages`. Disabled/null configurations add no font and do not set the system default family. QML still loads without OPPO Sans; the font is not a login requirement.

```nix
programs.kaltsit-sddm = {
  enable = true;
  fontFile = /absolute/private/path/OPPO-Sans-4.0.ttf;
};
```

Obtain the font and check its license separately. The project neither downloads, publicly distributes nor modifies it, and has not verified a license conclusion from the handoff's secondary reporting. An absolute path outside the flake requires `--impure` for future evaluation/builds (for example `nixos-rebuild build --impure --flake /path/to/system#host`); do not commit the font to a public repository to bypass this restriction. Explicit use imports the file into the local Nix store and the built system's font collection; avoid uploading font-containing outputs to a public cache. Development first loaded the font in a test VM, then deployed it through the system font configuration at the user’s request; the font binary remains local.

For initial activation on a new machine, retain known-good configuration and a previous generation, complete VM checks below, then configure the option and run:

```sh
sudo nixos-rebuild build --flake /path/to/system#host
sudo nixos-rebuild boot --flake /path/to/system#host
# Reboot when convenient; activate on the next boot, not with switch initially.
```

These are instructions for a new environment. The development build was deployed using build then boot; publication does not switch the host again. See the [v1.4 release record](V1.4-RELEASE.md) for deployment versus validation scope. Historical stage reports below retain their original time context.

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

Append `--font-file /absolute/private/path/OPPO-Sans-4.0.ttf` and use a separate `--output` directory to test the font-enabled mode. The runner copies it only into its private HOME with a separate fontconfig cache. Omit the argument to test the system-font fallback; keep the output directories separate.

It loads the real greeter with `--test-mode --theme` and ends that process after six seconds, then sends actual key and mouse events through the matching `qmltestrunner` with mock SDDM models. Each run has 17 behavior checks covering zero/one/multiple users, manual usernames, sessions, Tab/Return/Esc, duplicate submissions, password clearing, errors and power calls. Layouts are checked at 1280×800/100%, 1920×1080/100% and 3120×2080/175%.

The output root contains `results.json`. Resolution subdirectories contain native PNGs for a single user, errors, multiple-user lists, long usernames, session lists, empty user models, avatar/keyboard focus and a background-only frame, plus per-region `contrast.json` and glyph-edge `alignment.json`. These are native Qt renders with mocks, not authentication evidence. At 175%, Qt rounds the logical capture size and produces a raw 3120×2081 PNG. The report records requested layout, logical size and captured pixels separately; it does not crop or resize away that difference.

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

## v6 local font and actual validation

On 2026-11-02 (America/Los_Angeles), runtime QML, module and build source were `88b9b971e9b5f42fe71a851f52346a899e7b1674`; the package remains 1.3.0. Phase-one `python3 -m unittest discover -s tests -v` actually returned `Ran 108 tests in 49.435s / OK`, exit 0. `nix flake check --no-write-lock-file path:.` returned `all checks passed!`, exit 0. Two unit tests were added relative to v5 to accept aligned images and reject displacement, missing ink and wrong dimensions; existing contrast and preview tests were updated. Nix evaluation checks cover default-null fontFile, no font effect while disabled, one local font package when enabled with a path, and explicit user theme precedence.

The local font package was actually built; source and packaged font SHA-256 both equal `6c7d5864c661516e1f400d9f21e4297f2e2a0719909691e29607cc4ef484a9f4`. An initial build exposed an absolute string path not imported into the build sandbox; explicitly importing it with `builtins.path` fixed the build. Evaluation alone was not counted as font-build evidence.

Real greeter test-mode loaded both with and without the font in private HOME/D-Bus/offscreen software environments. Each mode ran 17 QtTest behaviors at three sizes, 102 checks total, all exit 0. Font/clock metrics and footer grouping add two behaviors per layout to v5's 15 retained interactions. Actual Qt `fontInfo` reports OPPO Sans 4.0, clock 400, username/buttons 500 and labels 400. Without the font it resolves to system Noto Sans. The single-user avatar and keyboard layout remain read-only focus stops.

Native normal/error/long-name/list/focus captures were inspected without observed overlap or overflow. The alignment checker identifies leftmost ink against an independent same-size background using summed RGB difference >60 and a 1.5 logical-pixel tolerance. Clock prefixes 00, 10, 17 and 23 were checked, avoiding a single-digit hardcoded offset. Maximum drift is 1px at 1280×800 and 1920×1080 (error outline), and 0.571429px at 175%. VM normal/no-font clock, date, avatar, field border and first footer label all start at x=72; the error outline starts at x=71. The empty container gap matches the wallpaper pixel for pixel.

### Contrast and sampling

The table uses actual font-enabled control coordinates and independent Qt background frames, taking each region's minimum over six states. Required ratios are ≥4.5:1 for text and ≥3:1 for focus; label alpha 0.8 participates in compositing. The no-font mode independently passed the same checks. Unoutlined white/red text can still fail: raw values remain visible and are not counted as passes. The local-outline backdrop rationale and antialiasing limitations are the same as v5.

| Region | 1280×800 / 100% | 1920×1080 / 100% | 3120×2080 / 175% |
|---|---:|---:|---:|
| Clock | 10.619 | 10.196 | 11.455 |
| Date | 9.264 | 8.911 | 11.012 |
| Username / outline | 8.070 | 8.980 | 8.393 |
| Input text | 11.953 | 11.953 | 11.953 |
| Placeholder | 4.890 | 4.890 | 4.890 |
| Error / outline | 5.440 | 5.395 | 5.490 |
| Session value / outline | 10.437 | 11.647 | 11.111 |
| Keyboard value / outline | 9.807 | 11.300 | 10.736 |
| Shutdown / outline | 8.946 | 11.060 | 9.962 |
| Reboot / outline | 8.525 | 10.437 | 9.525 |
| Session label / outline (alpha 0.8) | 6.870 | 7.575 | 7.242 |
| Keyboard label / outline (alpha 0.8) | 6.507 | 7.349 | 7.053 |
| Minimum focus | 5.234 | 5.200 | 5.292 |
| Raw username (no outline) | 1.003 | 1.559 | 1.180 |
| Raw error (no outline) | 1.001 | 1.003 | 1.001 |
| Minimum raw footer (no outline) | 1.249 | 3.274 | 1.964 |

Sampling uses every distinct RGB inside each actual rectangle, not an average. Logical boxes below are (x,y,width,height); physical boxes use floor(left/top×scale) and ceil(right/bottom×scale). For the fixed 3840×2160 source, f=max(W/3840,H/2160), offsets=((3840f−W)/2,(2160f−H)/2), and source coordinates=(physical+offset)/f. Every run writes the exact logical, physical and source rectangles, darkest/lightest RGB/luminance, raw/outlined extrema and minimum ratios to `contrast.json`. The table records normal controls and the error-state error row; expanded states are also checked in that JSON.

| Size / region | Logical rectangle | Darkest RGB (luminance) | Lightest RGB (luminance) |
|---|---|---|---|
| 1280x800-1 / Clock | (72, 71.75, 186, 55) | `#ddede0` (0.813223) | `#f6fffd` (0.982047) |
| 1280x800-1 / Date | (72, 152.25, 175, 18) | `#cedfcd` (0.703049) | `#ecfcf1` (0.938045) |
| 1280x800-1 / Username | (134, 361, 226, 48) | `#566544` (0.117031) | `#eef6eb` (0.900868) |
| 1280x800-1 / Error | (72, 477, 288, 18) | `#38352e` (0.035842) | `#d8e1d0` (0.730034) |
| 1280x800-1 / Session | (61, 479, 125.641, 32) | `#37342d` (0.034577) | `#646963` (0.137133) |
| 1280x800-1 / Keyboard | (186.641, 479, 70.172, 32) | `#5a6158` (0.114276) | `#8f9a8c` (0.308443) |
| 1280x800-1 / Shutdown | (268.812, 479, 49.594, 32) | `#97a291` (0.344643) | `#c2cbb8` (0.576419) |
| 1280x800-1 / Reboot | (318.406, 479, 49.594, 32) | `#bdc6b3` (0.544617) | `#dbe3d4` (0.747517) |
| 1920x1080-1 / Clock | (72, 71.75, 186, 55) | `#d8e9d9` (0.778865) | `#edfbee` (0.931719) |
| 1920x1080-1 / Date | (72, 152.25, 175, 18) | `#cadbc9` (0.674366) | `#e1f1e4` (0.845196) |
| 1920x1080-1 / Username | (134, 487, 226, 48) | `#313c2c` (0.040665) | `#92a47e` (0.341683) |
| 1920x1080-1 / Error | (72, 603, 288, 18) | `#32312d` (0.030642) | `#65735a` (0.157664) |
| 1920x1080-1 / Session | (61, 605, 125.641, 32) | `#33322e` (0.031823) | `#43423e` (0.054375) |
| 1920x1080-1 / Keyboard | (186.641, 605, 70.172, 32) | `#353430` (0.034263) | `#444c3f` (0.067567) |
| 1920x1080-1 / Shutdown | (268.812, 605, 49.594, 32) | `#454d41` (0.069546) | `#55614d` (0.110165) |
| 1920x1080-1 / Reboot | (318.406, 605, 49.594, 32) | `#51594e` (0.094441) | `#68765d` (0.166902) |
| 3120x2080-1.75 / Clock | (72, 71.75, 186, 55) | `#e7f5e8` (0.881199) | `#f3fff5` (0.971673) |
| 3120x2080-1.75 / Date | (72, 152.25, 175, 18) | `#e1f1e4` (0.845196) | `#effdf0` (0.948926) |
| 3120x2080-1.75 / Username | (134, 536, 226, 48) | `#5b6d42` (0.135548) | `#cfdac9` (0.676253) |
| 3120x2080-1.75 / Error | (72, 652, 288, 18) | `#3e423a` (0.052261) | `#aab79d` (0.448473) |
| 3120x2080-1.75 / Session | (61, 654, 125.641, 32) | `#3d413c` (0.050989) | `#5a664e` (0.122265) |
| 3120x2080-1.75 / Keyboard | (186.641, 654, 70.172, 32) | `#525d4d` (0.101584) | `#728162` (0.201598) |
| 3120x2080-1.75 / Shutdown | (268.812, 654, 49.594, 32) | `#727e65` (0.194387) | `#92a184` (0.332667) |
| 3120x2080-1.75 / Reboot | (318.406, 654, 49.594, 32) | `#8d9b81` (0.306904) | `#b1bda5` (0.484589) |

### VM captures and differences from the design reference

The existing NixOS 26.05 / SDDM 0.21.0 / Qt 6.11.2 / 1280×800 / X11/xterm VM runner was reused with a fresh temporary disk; build-vm was not rerun. Only built theme and local-font-package outputs were copied into the guest. No host HOME sharing or host theme activation occurred. Guest fontconfig listed OPPO and its named weights; the greeter process mapped the font file. A no-font capture was taken first. With the font loaded, the run exercised real wrong-password rejection, fixture-password PAM login into xterm, logout, real multiple-user listing and broken-QML embedded fallback. Authentication was not repeated inside fallback; the no-font capture proves loading, not a separate PAM login.

The first VM attempt passed login/logout but stopped because the external harness assumed `/etc/sddm.conf` existed; this guest uses `/etc/sddm.conf.d/`. After correcting the harness, the complete flow passed on a new disk with exit 0. This was not a host configuration change; the failed attempt was retained.

New original QEMU PNGs: [normal](../previews/sddm/login-v6.png), [wrong password](../previews/sddm/login-v6-error.png), [long session/shutdown focus](../previews/sddm/login-v6-long-session.png), [no-font fallback](../previews/sddm/login-v6-nofont.png), [multiple users](../previews/sddm/login-v6-multiuser.png). All five are unprocessed 1280×800/100% captures. The manifest appends files, SHA-256, source and font provenance without changing prior images/entries. Only tester authenticated; preview2 is a locked temporary guest account. The long-name image renames the guest's xterm display label to “Plasma (Wayland)”; it does not validate a Plasma session.

Compared with the [Chromium references](design/sddm-v6-mockups/README.en.md), primary positions and optical left edges match, but Qt rasterization, numeral/text widths and outlines differ. Qt power buttons have a natural width of about 49.594px; the long session elides earlier (visibly “Plasma (…”) and shutdown focus sits slightly further left. Text was not compressed to hide that difference. Stronger dark glyph outlines and a dark outer focus edge are retained; errors still use the existing red with white outline. The real VM clock shows capture time; references are fixed at 17:05. Browser mockups were not counted as test evidence.

Complete shutdown/reboot were not retested; the initial failed flow remains unresolved. The harness stopped its own VM process, which is not a successful shutdown test. Physical hardware, a real high-DPI greeter, multiple displays, TTY recovery and host activation are unverified. The 3:2/175% evidence is native Qt offscreen only (raw 3120×2081 due to logical-size rounding); no VM 3:2 capture was fabricated. The font was not committed or publicly distributed. No push, tag, Release or PR was made.

### Footer focus indicators in the VM

In a 3120×2080 Wayland VM at 175% scale, Tab moved focus through the session, keyboard layout, shutdown and reboot buttons in both the normal and error layouts. At each sample along the four straight sides, excluding the corners, we compared both lines with the adjacent wallpaper pixel and recorded the higher contrast.

| Minimum contrast per button | Session | Keyboard | Shutdown | Reboot |
|---|---:|---:|---:|---:|
| Normal layout | 6.9847:1 | 4.2254:1 | 3.6157:1 | 4.3905:1 |
| Error layout | 7.3707:1 | 4.6048:1 | 3.5991:1 | 4.1774:1 |

Before the fix, the shutdown indicator in the error layout reached a minimum of 2.8358:1. All eight original frames with the fix meet the 3:1 wallpaper threshold along the straight edges. The lowest contrast between the two lines was 12.9167:1, above the 9:1 threshold. The earlier v5 table measures offscreen compositing in the older theme. Its focus values use a different measurement from these VM screen pixels.

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

This is an experimental Qt 6 login theme. Physical hardware, boot-menu rollback, TTY recovery, multiple displays, special input methods and assistive authentication are unverified. The system needs a font supporting Chinese; optional `fontFile` only installs the supplied font and does not change the default family.
Keyboard layout may appear as unknown in isolated Wayland test-mode; do not interpret it as a physical keyboard layout. SDDM/PAM controls actual authentication. There is no custom fingerprint, smart-card or multi-factor prompt interaction, and no claim of support for those environments.
