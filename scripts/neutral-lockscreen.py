#!/usr/bin/env python3
"""Build a theme-scoped rendering adjustment from the matching KDE packages.

Everything except the fader's three color factors is kept upstream. No
authentication, focus, event handling, or user input code is patched.
"""
from pathlib import Path
import json
import shutil
import sys

desktop, workspace, output = map(Path, sys.argv[1:])
shell = desktop / "share/plasma/shells/org.kde.plasma.desktop"
target = output / "share/plasma/shells/org.kde.plasma.desktop"
lock_ui = Path("contents/lockscreen/LockScreenUi.qml")
ui = (shell / lock_ui).read_text()
faders = list(workspace.glob("lib/qt-6/qml/org/kde/breeze/components/WallpaperFader.qml"))
if len(faders) != 1:
    raise SystemExit("Unsupported KDE package: expected one WallpaperFader.qml")
fader = faders[0].read_text()

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit(f"KDE lockscreen changed; review required before building: {old}")
    return text.replace(old, new, 1)

ui = replace_once(ui, "        WallpaperFader {", "        KaltsitWallpaperFader {")
fader = replace_once(fader, "    property real factor: 0", """    property real factor: 0
    // Only the Medical Green wallpaper opts out of color transformations.
    readonly property bool kaltsitOriginalColors: source && source.pluginName === "org.xinyan.kaltsit.medicalgreen.lock"
""".rstrip())
factors = {
    "contrast": "0.8 * wallpaperFader.factor + (1 - wallpaperFader.factor)",
    "saturation": "1.5 * wallpaperFader.factor + (1 - wallpaperFader.factor)",
    "intensity": "(wallpaperFader.lightColorScheme ? 1.6 : 0.7) * wallpaperFader.factor + (1 - wallpaperFader.factor)",
}
for key, value in factors.items():
    old = f"readonly property real {key}: {value}"
    fader = replace_once(fader, old, f"readonly property real {key}: wallpaperFader.kaltsitOriginalColors ? 1.0 : ({value})")

# A complete package is needed for Plasma/Shell resolution. Untouched files
# are copied byte for byte from the exact upstream package. KPackage rejects
# external symlinks for its lockscreen entry points.
target.mkdir(parents=True)
for path in shell.rglob("*"):
    relative = path.relative_to(shell)
    dest = target / relative
    if path.is_dir():
        dest.mkdir(exist_ok=True)
    elif relative != lock_ui:
        shutil.copyfile(path, dest)
(target / lock_ui).write_text(ui)
(target / lock_ui.parent / "KaltsitWallpaperFader.qml").write_text(fader)
manifest = {
    "plasma_desktop": str(desktop), "plasma_workspace": str(workspace),
    "scope": "org.xinyan.kaltsit.medicalgreen.lock",
    "color_factors": {key: 1.0 for key in factors},
    "blur_and_authentication": "unchanged upstream",
}
(output / "share/doc/kaltsit-theme/lockscreen-rendering.json").write_text(json.dumps(manifest, indent=2) + "\n")
