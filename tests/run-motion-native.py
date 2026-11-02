#!/usr/bin/env python3
"""Native Qt playback checks; every run owns a fresh D-Bus and fake services.

Use --backend software for static fallback, offscreen-rhi to probe offscreen
OpenGL, or rhi inside tests' private KWin session. Needs Python dbus-next.
No daily-session service is addressed. The fake service never authenticates,
changes a physical power supply, or calls a real lock/power API.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


async def run_native(args, env, script, video, repair):
    from dbus_next.aio import MessageBus
    from dbus_next.service import ServiceInterface, method, signal

    class Power(ServiceInterface):
        def __init__(self):
            super().__init__('org.freedesktop.PowerManagement')
            self.value = False
        @method()
        def GetPowerSaveStatus(self) -> 'b':
            return self.value
        @signal()
        def PowerSaveStatusChanged(self, value) -> 'b':
            return value

    class Lock(ServiceInterface):
        def __init__(self):
            super().__init__('org.freedesktop.ScreenSaver')
            self.value = False
        @method()
        def GetActive(self) -> 'b':
            return self.value
        @signal()
        def ActiveChanged(self, value) -> 'b':
            return value

    daemon = await asyncio.create_subprocess_exec('dbus-daemon', '--session', '--nofork', '--print-address=1',
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env)
    bus = None
    process = None
    try:
        address = (await daemon.stdout.readline()).decode().strip()
        assert address, 'Private D-Bus did not start'
        env['DBUS_SESSION_BUS_ADDRESS'] = address
        bus = await MessageBus(bus_address=address).connect()
        power, lock = Power(), Lock()
        bus.export('/org/freedesktop/PowerManagement', power)
        bus.export('/ScreenSaver', lock)
        bus.export('/org/freedesktop/ScreenSaver', lock)

        class Control(ServiceInterface):
            def __init__(self):
                super().__init__('org.kaltsit.MotionTest')
            @method()
            async def Connect(self):
                await bus.request_name(power.name)
                await bus.request_name(lock.name)
            @method()
            def Battery(self, value: 'b'):
                power.value = value
                power.PowerSaveStatusChanged(value)
            @method()
            def Locked(self, value: 'b'):
                lock.value = value
                lock.ActiveChanged(value)
            @method()
            async def DropPower(self):
                await bus.release_name(power.name)
            @method()
            async def DropLock(self):
                await bus.release_name(lock.name)
            @method()
            async def ReconnectPower(self):
                power.value = False
                await bus.request_name(power.name)
            @method()
            async def ReconnectLock(self):
                lock.value = False
                await bus.request_name(lock.name)
            @method()
            def Repair(self):
                shutil.copyfile(video, repair)

        control = Control()
        bus.export('/Test', control)
        await bus.request_name(control.name)
        process = await asyncio.create_subprocess_exec(args.qml, '-f', str(script), env=env,
                                                       stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        output, _ = await asyncio.wait_for(process.communicate(), timeout=160)
        return process.returncode, output.decode('utf-8', errors='replace')
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        if bus is not None:
            bus.disconnect()
        daemon.terminate()
        await daemon.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--qml', default='qml')
    parser.add_argument('--backend', choices=['software', 'rhi', 'offscreen-rhi'], default='software')
    parser.add_argument('--video', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    ui = args.package.resolve() / 'share/plasma/wallpapers/org.xinyan.kaltsit.medicalgreen.motion/contents/ui'
    assert (ui / 'VideoSurface.qml').is_file(), 'Not an installed motion package'
    video = json.loads(re.search(r'var video = (.*);', (ui / 'Defaults.js').read_text(encoding='utf-8'))[1])
    if args.video:
        video = args.video.resolve(strict=True).as_uri()
    assert video, 'Pass --video or build the addon with videoFile'
    from urllib.parse import unquote, urlparse
    video_path = Path(unquote(urlparse(video).path)).resolve(strict=True)
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
        if args.backend != 'rhi':
            (scratch / 'home').mkdir(mode=0o700)
            (scratch / 'runtime').mkdir(mode=0o700)
            env.update(HOME=str(scratch/'home'), XDG_RUNTIME_DIR=str(scratch/'runtime'),
                       XDG_CONFIG_HOME=str(scratch/'home/.config'), XDG_CACHE_HOME=str(scratch/'home/.cache'),
                       XDG_DATA_HOME=str(scratch/'home/.local/share'), XDG_STATE_HOME=str(scratch/'home/.local/state'),
                       QT_QPA_PLATFORM='offscreen')
            if args.backend == 'software':
                env['QT_QUICK_BACKEND'] = 'software'
            else:
                env.pop('QT_QUICK_BACKEND', None)
                env.update(LIBGL_ALWAYS_SOFTWARE='1', QSG_RHI_BACKEND='opengl')
            for key in ['DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS', 'SESSION_MANAGER']:
                env.pop(key, None)
        env.update(QT_FORCE_STDERR_LOGGING='1', QT_MEDIA_BACKEND='ffmpeg')
        repair = scratch/'repair.mp4'
        values = [(ui/'VideoSurface.qml').as_uri(), video,
                  (args.package.resolve()/'share/wallpapers/KaltsitMedicalGreenMotion/contents/images/poster.jpg').as_uri(),
                  str(output/'frame.png'), args.backend, (scratch/'missing.mp4').as_uri(), repair.as_uri()]
        harness = Path(__file__).with_name('motion-runtime.qml').read_text(encoding='utf-8')
        script = scratch/'check.qml'
        script.write_text(harness.replace('[] // MOTION_TEST_ARGUMENTS', json.dumps(values)), encoding='utf-8')
        code, log = asyncio.run(run_native(args, env, script, video_path, repair))
        (output/'runtime.log').write_text(log, encoding='utf-8')
        assert code == 0, log
        assert 'MOTION_TEST_PASS ' in log, log
        result = json.loads(log.split('MOTION_TEST_PASS ', 1)[1].splitlines()[0])
        (output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result))


if __name__ == '__main__':
    main()
