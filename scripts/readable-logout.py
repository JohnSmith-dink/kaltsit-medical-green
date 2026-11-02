#!/usr/bin/env python3
"""Use the palette background in the matching upstream logout confirmation.

Only the background rectangle changes. Buttons, signals, countdown and
keyboard handling remain byte-for-byte upstream; no power action runs here.
"""
from pathlib import Path
import json
import shutil
import sys


UPSTREAM_BACKGROUND = '''        // Intentionally hardcoded because any other color looks terrible here.
        // Any bug reports about illegible text or icons should be considered
        // a color scheme error and sent back to the user or their distro.
        color: "black"
        opacity: 0.85'''
PALETTE_BACKGROUND = '''        // Match the Complementary foreground, including light color schemes.
        color: Kirigami.Theme.backgroundColor
        opacity: 0.96'''


def render_logout(source):
    if source.count(UPSTREAM_BACKGROUND) != 1:
        raise ValueError("KDE logout background changed; review required before building")
    return source.replace(UPSTREAM_BACKGROUND, PALETTE_BACKGROUND, 1)


def install(workspace, output, version):
    source = workspace / "share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout"
    rendered = render_logout((source / "Logout.qml").read_text())
    destination = output / "share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout"
    shutil.copytree(source, destination, copy_function=shutil.copyfile)
    (destination / "Logout.qml").write_text(rendered)
    record = {
        "plasma_workspace": str(workspace),
        "plasma_workspace_version": version,
        "source": str(source),
        "license": "GPL-2.0-or-later; upstream SPDX headers retained",
        "background": "Kirigami.Theme.backgroundColor",
        "opacity": 0.96,
        "buttons_signals_countdown_keyboard": "unchanged upstream",
    }
    (output / "share/doc/kaltsit-theme/logout-rendering.json").write_text(
        json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    install(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
