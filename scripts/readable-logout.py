#!/usr/bin/env python3
"""Keep the upstream confirmation transparent, with local text/icon contrast.

Only visual declarations and local delegate names change. Power signals,
countdown and keyboard handling remain upstream; no power action runs here.
"""
from pathlib import Path
import json
import shutil
import sys


UPSTREAM_BACKGROUND = '''    Rectangle {
        id: backgroundRect
        anchors.fill: parent
        // Intentionally hardcoded because any other color looks terrible here.
        // Any bug reports about illegible text or icons should be considered
        // a color scheme error and sent back to the user or their distro.
        color: "black"
        opacity: 0.85
    }
'''
UPSTREAM_LABEL = "        PlasmaComponents.Label {\n"
OUTLINED_LABEL = UPSTREAM_LABEL + '''            style: Text.Outline
            styleColor: Kirigami.Theme.backgroundColor
'''
UPSTREAM_BUTTON_SURFACE = '''        color: root.softwareRendering ? Kirigami.Theme.backgroundColor : Kirigami.Theme.textColor
        opacity: {
            if (root.activeFocus || root.hovered) {
                return root.softwareRendering ? 0.8 : 0.15
            }
            return root.softwareRendering ? 0.6 : 0
        }'''
LOCAL_BUTTON_SURFACE = '''        color: Kirigami.Theme.backgroundColor
        opacity: 0.96
        border.color: Kirigami.Theme.focusColor
        border.width: root.activeFocus || root.hovered ? 2 : 0'''
UPSTREAM_BUTTON_TEXT = '''            style: root.softwareRendering ? Text.Outline : Text.Normal
            styleColor: Kirigami.Theme.backgroundColor // Unused without outline'''
LOCAL_BUTTON_TEXT = '''            style: Text.Outline
            styleColor: Kirigami.Theme.backgroundColor'''
UPSTREAM_USER_TEXT = '''        style: wrapper.softwareRendering ? Text.Outline : Text.Normal
        styleColor: wrapper.softwareRendering ? Kirigami.Theme.backgroundColor : "transparent" //no outline, doesn't matter'''
LOCAL_USER_TEXT = '''        style: Text.Outline
        styleColor: Kirigami.Theme.backgroundColor'''


def replace_exact(source, old, new, count=1):
    if source.count(old) != count:
        raise ValueError("KDE logout rendering changed; review required before building")
    return source.replace(old, new)


def render_logout(source):
    source = replace_exact(source, UPSTREAM_BACKGROUND, "")
    source = replace_exact(source, "    UserDelegate {", "    KaltsitLogoutUserDelegate {")
    return replace_exact(source, UPSTREAM_LABEL, OUTLINED_LABEL, 5)


def render_button(source):
    return replace_exact(source, "\nActionButton {", "\nKaltsitLogoutActionButton {")


def render_action(source):
    source = replace_exact(source, UPSTREAM_BUTTON_SURFACE, LOCAL_BUTTON_SURFACE)
    return replace_exact(source, UPSTREAM_BUTTON_TEXT, LOCAL_BUTTON_TEXT)


def render_user(source):
    return replace_exact(source, UPSTREAM_USER_TEXT, LOCAL_USER_TEXT)


def install(workspace, output, version):
    source = workspace / "share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout"
    components = workspace / "lib/qt-6/qml/org/kde/breeze/components"
    # Validate all anchors before creating any output. Never patch shared KDE files.
    rendered = {
        "Logout.qml": render_logout((source / "Logout.qml").read_text()),
        "LogoutButton.qml": render_button((source / "LogoutButton.qml").read_text()),
        "KaltsitLogoutActionButton.qml": render_action((components / "ActionButton.qml").read_text()),
        "KaltsitLogoutUserDelegate.qml": render_user((components / "UserDelegate.qml").read_text()),
    }
    destination = output / "share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout"
    shutil.copytree(source, destination, copy_function=shutil.copyfile)
    # copytree also preserves the Nix store directory's read-only mode.
    destination.chmod(destination.stat().st_mode | 0o200)
    for name, content in rendered.items():
        (destination / name).write_text(content)
    record = {
        "plasma_workspace": str(workspace),
        "plasma_workspace_version": version,
        "source": str(source),
        "components": str(components),
        "license": "GPL-2.0-or-later / LGPL-2.0-or-later; upstream SPDX headers retained",
        "fullscreen_background": "removed",
        "text": "palette foreground with palette background Text.Outline",
        "icon_discs": "palette background, opacity 0.96, local focus border",
        "buttons_signals_countdown_keyboard": "unchanged upstream",
    }
    (output / "share/doc/kaltsit-theme/logout-rendering.json").write_text(
        json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    install(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
