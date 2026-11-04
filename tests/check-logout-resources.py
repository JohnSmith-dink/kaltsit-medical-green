#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check the installed confirmation against its actual KDE input."""
from pathlib import Path
import sys


def check_handlers(before, after):
    # Compare the complete signals, update choices, Escape action and timer.
    assert before.split('    Rectangle {\n        id: backgroundRect', 1)[0] == after.split('    MouseArea {', 1)[0]
    mouse = '    MouseArea {'
    assert before.split(mouse, 1)[1].split('    UserDelegate {', 1)[0] == after.split(mouse, 1)[1].split('    LeftConfirmation {', 1)[0]
    # All original button instances, their visibility, focus, navigation,
    # and onClicked handlers must be identical apart from their font family.
    start = '            LogoutButton {\n'
    assert start in before and start in after
    assert before[before.index(start):] == after[after.index(start):].replace('                font.family: column.displayFamily\n', '')


def check(workspace, output):
    upstream = workspace / 'share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout'
    theme = output / 'share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout'
    lock = output / 'share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen'
    check_handlers((upstream/'Logout.qml').read_text(), (theme/'Logout.qml').read_text())
    for base in (upstream, theme):
        assert '    Keys.onPressed:' in (base/'LogoutButton.qml').read_text()
    assert (upstream/'LogoutButton.qml').read_text().split('    Keys.onPressed:')[1] == (theme/'LogoutButton.qml').read_text().split('    Keys.onPressed:')[1]
    assert (upstream/'timer.js').read_bytes() == (theme/'timer.js').read_bytes()
    for name in ('MedicalClock.qml', 'MedicalPalette.js'):
        assert (theme/name).read_bytes() == (lock/name).read_bytes(), name
    print('KDE confirmation handlers and timer preserved; clock and palette match desktop lock.')


if __name__ == '__main__':
    check(*map(Path, sys.argv[1:]))
