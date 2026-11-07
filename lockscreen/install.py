#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Install visual variants of the matching Plasma shell's lock screen."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def install(output):
    assets = Path(__file__).resolve().parent
    directory = output / 'share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen'
    for original, variant in [('LockScreenUi', 'MedicalLockScreenUi'),
                              ('MainBlock', 'MedicalMainBlock'),
                              ('NoPasswordUnlock', 'MedicalNoPasswordUnlock')]:
        shutil.copyfile(directory / (original + '.qml'), directory / (variant + '.qml'))
    with (assets / 'layout.patch').open('rb') as patch:
        subprocess.run(['patch', '-p1', '--fuzz=0', '--forward', '--batch'],
                       cwd=directory, stdin=patch, check=True)
    for component in assets.glob('*.qml'):
        shutil.copyfile(component, directory / component.name)
    subprocess.run([sys.executable, assets.parent / 'sddm/build-palette.py',
                    output / 'share/color-schemes/KaltsitMedicalGreen.colors',
                    directory / 'MedicalPalette.js'], check=True)

    record_path = output / 'share/doc/kaltsit-theme/lockscreen-rendering.json'
    record = json.loads(record_path.read_text())
    record.update(layout='SDDM v6 left column',
                  blur_and_authentication='Medical Green: no wallpaper blur; native KScreenLocker authentication')
    record_path.write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    install(Path(sys.argv[1]))
