#!/usr/bin/env python3
"""Load real greeter test-mode and check UI with mocks, in private HOME/D-Bus.

The UI screenshot is explicitly mocked; neither check authenticates a user.
"""
import argparse
import json
import os
from pathlib import Path
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
                 QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_FORCE_STDERR_LOGGING='1')
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
        script=scratch/'check.qml'
        values=[(theme/'Main.qml').as_uri(),str(output/'ui-mock.png')]
        script.write_text(Path(__file__).with_name('sddm-runtime.qml').read_text().replace('[] // SDDM_TEST_ARGUMENTS',json.dumps(values)))
        result=subprocess.run(['dbus-run-session','--',args.qml,'-f',str(script)],env=env,capture_output=True,timeout=15)
        log=(result.stdout+result.stderr).decode('utf-8',errors='replace')
        (output/'ui-mock.log').write_text(log)
        assert result.returncode==0 and 'SDDM_UI_PASS ' in log,log
        checks=json.loads(log.split('SDDM_UI_PASS ',1)[1].splitlines()[0])
        report=dict(greeter_test_mode_loaded=True,ui_mock_checks=checks,authentication_tested=False,
                    power_actions_tested=False,screenshot_kind='offscreen UI with mock SDDM models')
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))


if __name__=='__main__':
    main()
