#!/usr/bin/env python3
"""Install the KDE confirmation with the theme's lock wallpaper and left column."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ASSETS = Path(__file__).resolve().parents[1] / 'logout'
THEME = 'share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout'
LOCK = 'share/plasma/shells/org.kde.plasma.desktop/contents/lockscreen'
WALLPAPER = 'share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg'


def install(workspace, output, version):
    upstream = workspace / 'share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout'
    target = output / THEME
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as scratch:
        staged = Path(scratch) / 'logout'
        shutil.copytree(upstream, staged, copy_function=shutil.copyfile)
        staged.chmod(staged.stat().st_mode | 0o200)
        with (ASSETS / 'layout.patch').open('rb') as patch:
            result = subprocess.run(['patch', '-p1', '--fuzz=0', '--batch', '--forward'],
                                    cwd=staged, stdin=patch, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('KDE logout layout changed; review required before building:\n'
                             + result.stdout + result.stderr)
        for component in ASSETS.glob('*.qml'):
            shutil.copyfile(component, staged / component.name)
        # KPackage resources must stay inside their package. Install the exact
        # same clock and palette rather than maintaining another copy in source.
        for name in ('MedicalClock.qml', 'MedicalPalette.js'):
            shutil.copyfile(output / LOCK / name, staged / name)
        shutil.copyfile(output / WALLPAPER, staged / 'LockWallpaper.jpg')
        staged.rename(target)

    record = {
        'plasma_workspace': str(workspace),
        'plasma_workspace_version': version,
        'source': str(upstream),
        'license': 'Upstream GPL-2.0-or-later headers retained; original layout components MIT',
        'fullscreen_background': '锁屏壁纸（主题自带图，原亮度）',
        'layout': 'SDDM v6 left column with the desktop lock clock',
        'buttons_signals_countdown_keyboard': 'unchanged upstream handlers',
    }
    (output / 'share/doc/kaltsit-theme/logout-rendering.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    install(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
