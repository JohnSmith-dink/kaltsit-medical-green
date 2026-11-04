#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare the packaged lock-screen authentication paths to the linked KDE source."""
from pathlib import Path
import sys


def section(text, begin, end):
    return text[text.index(begin):text.index(end, text.index(begin))]


def check(kde, installed):
    relative = Path('share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen')
    upstream, output = kde / relative, installed / relative
    for name in ('MainBlock.qml', 'NoPasswordUnlock.qml', 'PasswordSync.qml'):
        assert (output / name).read_bytes() == (upstream / name).read_bytes(), name
    original = (upstream / 'LockScreenUi.qml').read_text()
    medical = (output / 'MedicalLockScreenUi.qml').read_text().replace('MedicalNoPasswordUnlock.qml', 'NoPasswordUnlock.qml')
    # Check whole handlers, including failure, success without a typed password,
    # clearing on suspend, input wakeup, grace periods and the password response.
    for begin, end, replacement_end in [
        ('    Connections {', '    SessionManagement {', '    SessionManagement {'),
        ('    Connections {\n        target: sessionManagement', '        WallpaperFader {',
         '        // The greeter already puts'),
        ('                onPasswordResult:', '                actionItems:', '                actionItems:'),
    ]:
        assert section(original, begin, end) == section(medical, begin, replacement_end), begin
    original = (upstream / 'MainBlock.qml').read_text()
    medical = (output / 'MedicalMainBlock.qml').read_text()
    for begin, end in [('    onUserSelected:', '\n    RowLayout {'),
                       ('            text: PasswordSync.password','            placeholderText:'),
                       ('            focus: true', '        PlasmaComponents3.Button {'),
                       ('            onClicked: sessionManager.startLogin()', '    component FailableLabel'),
                       ('        RejectPasswordAnimation {', '    FailableLabel {')]:
        assert section(original, begin, end) == section(medical, begin, end.replace('RowLayout {', 'Item {')), begin
    no_prompt = (output / 'MedicalNoPasswordUnlock.qml').read_text()
    assert no_prompt.replace('MedicalSession {', 'SessionManagementScreen {') == (upstream / 'NoPasswordUnlock.qml').read_text()
    print('Packaged Plasma authentication, password synchronization and wake handlers match KDE.')


if __name__ == '__main__':
    check(*map(Path, sys.argv[1:]))
