#!/usr/bin/env python3
"""Load real greeter test-mode and check UI with mocks, in private HOME/D-Bus.

The UI screenshot is explicitly mocked; neither check authenticates a user.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    parser.add_argument('--greeter',default='sddm-greeter-qt6')
    parser.add_argument('--qml',default='qml')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    theme=args.package.resolve()/'share/sddm/themes/KaltsitMedicalGreen'
    assert (theme/'Main.qml').is_file(), 'Not an installed SDDM theme package'
    args.output.mkdir(parents=True,exist_ok=True)
    output=args.output.resolve()
    with tempfile.TemporaryDirectory(prefix='kaltsit-sddm-native-') as scratch:
        scratch=Path(scratch)
        (scratch/'home').mkdir(); (scratch/'runtime').mkdir(mode=0o700)
        env=dict(os.environ,HOME=str(scratch/'home'),XDG_RUNTIME_DIR=str(scratch/'runtime'),
                 XDG_CONFIG_HOME=str(scratch/'home/.config'),XDG_DATA_HOME=str(scratch/'home/.local/share'),
                 XDG_CACHE_HOME=str(scratch/'home/.cache'),XDG_STATE_HOME=str(scratch/'home/.local/state'),
                 QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_FORCE_STDERR_LOGGING='1',
                 QT_SCALE_FACTOR='1')
        for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_PLUGIN_PATH','SESSION_MANAGER'):
            env.pop(key,None)
        with (output/'greeter-test-mode.log').open('w') as log:
            proc=subprocess.Popen(['dbus-run-session','--',args.greeter,'--test-mode','--theme',str(theme)],
                                  stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:
                code=proc.wait(timeout=6)
                raise AssertionError(f'Greeter exited early ({code}); see greeter-test-mode.log')
            except subprocess.TimeoutExpired:
                pass
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGTERM)
                    proc.wait(timeout=10)
        log=(output/'greeter-test-mode.log').read_text()
        assert 'Loading' in log and 'Main.qml' in log,log
        assert not any(term in log for term in ('Fallback to embedded theme','ReferenceError','TypeError',
                                               'is not installed','Cannot assign','is not a type')),log
        # QtTest sends QKeyEvent/QMouseEvent through the real Qt focus/event path.
        qml=Path(shutil.which(args.qml) or args.qml)
        runner=qml.with_name('qmltestrunner')
        assert runner.is_file(), f'Matching qmltestrunner is missing: {runner}'
        source=Path(__file__).with_name('sddm-runtime.qml').read_text()
        matrix=[]
        for width,height,scale in ((1280,800,1),(1920,1080,1),(3120,2080,1.75)):
            destination=output/f'{width}x{height}-{scale}'
            destination.mkdir(exist_ok=True)
            script=scratch/'tst_sddm.qml'
            values=[(theme/'Main.qml').as_uri(),str(destination),width,height,scale]
            script.write_text(source.replace('[] // SDDM_TEST_ARGUMENTS',json.dumps(values)))
            env['QT_SCALE_FACTOR']=str(scale)
            result=subprocess.run(['dbus-run-session','--',str(runner),'-input',str(script),'-o','-,txt'],
                                  env=env,capture_output=True,timeout=90)
            log=(result.stdout+result.stderr).decode('utf-8',errors='replace')
            (destination/'ui-mock.log').write_text(log)
            assert result.returncode==0 and '0 failed' in log,log
            assert not any(term in log for term in ('ReferenceError','TypeError','Cannot assign','is not installed')),log
            checks=re.findall(r'PASS\s+: .*::(test_\w+)\(\)',log)
            assert checks, 'No UI behavior checks ran'
            from PIL import Image
            # grabToImage takes an integer logical QSize, then applies DPR.
            # Keep the raw extra row at 175%; never crop/resample evidence.
            capture_size=tuple(int(int(d/scale+0.5)*scale+0.5) for d in (width,height))
            assert all(abs(actual-requested)<=1 for actual,requested in zip(capture_size,(width,height)))
            for name in ('single-user','error','multi-user-menu','long-username'):
                with Image.open(destination/(name+'.png')) as capture:
                    assert capture.size==capture_size,(name,capture.size)
            matrix.append(dict(layout_pixels=[width,height],scale=scale,capture_pixels=capture_size,
                               logical_surface=[width/scale,height/scale],checks=checks,exit_code=result.returncode))
        report=dict(greeter_test_mode_loaded=True,ui_mock_matrix=matrix,authentication_tested=False,
                    actual_power_actions_tested=False,screenshot_kind='native offscreen Qt with mock SDDM models',
                    keyboard_events='QtTest keyClick; real QKeyEvent dispatch',
                    screenshot_capture='QQuickItem grabToImage; logical QSize/DPR rounding recorded; no postprocessing')
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))


if __name__=='__main__':
    main()
