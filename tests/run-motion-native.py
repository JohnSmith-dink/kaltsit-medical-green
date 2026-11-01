#!/usr/bin/env python3
"""Run behavior checks against an installed addon in an isolated Qt environment.

Example (the caller supplies matching Qt/KDE QML imports):
  python3 tests/run-motion-native.py /nix/store/...-kaltsit-motion-* \
    --qml /path/to/qml --backend software --output /tmp/motion-result

RHI mode additionally requires a private KWin session and explicit private HOME,
XDG_RUNTIME_DIR, DBUS_SESSION_BUS_ADDRESS and WAYLAND_DISPLAY. This runner never
starts or changes a daily Plasma session.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--qml', default='qml')
    parser.add_argument('--backend', choices=['software', 'rhi'], default='software')
    parser.add_argument('--video', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ui = args.package.resolve() / 'share/plasma/wallpapers/org.xinyan.kaltsit.medicalgreen.motion/contents/ui'
    assert (ui / 'VideoSurface.qml').is_file(), 'Not an installed motion package'
    video = json.loads(re.search(r'var video = (.*);', (ui / 'Defaults.js').read_text(encoding='utf-8'))[1])
    if args.video:
        video = args.video.resolve(strict=True).as_uri()
    assert video, 'Pass --video or build the addon with videoFile'
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve()
    env = dict(os.environ)
    if args.backend == 'rhi':
        private = Path(env.get('KALTSIT_TEST_ROOT', '/nonexistent'))
        assert str(private).startswith('/tmp/kt13-motion-'), 'RHI checks require an isolated session'
        assert env.get('HOME') == str(private / 'home')
        assert env.get('XDG_RUNTIME_DIR') == str(private / 'runtime')
        assert env.get('WAYLAND_DISPLAY') == 'kaltsit-test' and env.get('DBUS_SESSION_BUS_ADDRESS')
    with tempfile.TemporaryDirectory(prefix='kaltsit-motion-check-') as scratch:
        scratch = Path(scratch)
        if args.backend == 'software':
            (scratch / 'home').mkdir(mode=0o700)
            (scratch / 'runtime').mkdir(mode=0o700)
            env.update(HOME=str(scratch/'home'), XDG_RUNTIME_DIR=str(scratch/'runtime'),
                       XDG_CONFIG_HOME=str(scratch/'home/.config'), XDG_CACHE_HOME=str(scratch/'home/.cache'),
                       XDG_DATA_HOME=str(scratch/'home/.local/share'), XDG_STATE_HOME=str(scratch/'home/.local/state'),
                       QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software')
            for key in ['DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'SESSION_MANAGER']:
                env.pop(key, None)
        env['QT_FORCE_STDERR_LOGGING'] = '1'
        env['QT_MEDIA_BACKEND'] = 'ffmpeg'
        values = [(ui/'VideoSurface.qml').as_uri(), video,
                  (args.package.resolve()/'share/wallpapers/KaltsitMedicalGreenMotion/contents/images/poster.jpg').as_uri(),
                  str(output/'frame.png'), args.backend]
        harness = Path(__file__).with_name('motion-runtime.qml').read_text(encoding='utf-8')
        harness = harness.replace('[] // MOTION_TEST_ARGUMENTS', json.dumps(values))
        script = scratch/'check.qml'
        script.write_text(harness, encoding='utf-8')
        result = subprocess.run([args.qml, '-f', str(script)], env=env, capture_output=True, timeout=160)
        log = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        (output/'runtime.log').write_text(log, encoding='utf-8')
        assert result.returncode == 0, log
        assert 'MOTION_TEST_PASS ' in log, log
        print(log.split('MOTION_TEST_PASS ', 1)[1].splitlines()[0])


if __name__ == '__main__':
    main()
