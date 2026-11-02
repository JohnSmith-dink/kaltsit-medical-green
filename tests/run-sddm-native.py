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
            for name in ('single-user','error','multi-user-menu','long-username','session-menu','empty-users','focus-user','focus-keyboard','background'):
                with Image.open(destination/(name+'.png')) as capture:
                    assert capture.size==capture_size,(name,capture.size)
            from test_sddm import sample_region, assert_sample, palette_module
            colors=palette_module.palette(Path(__file__).resolve().parents[1]/'share/color-schemes/KaltsitMedicalGreen.colors')
            runtime=(theme/'Main.qml').read_text()
            alpha=lambda name:float(re.search(r'readonly property real '+name+r':\s*([0-9.]+)',runtime)[1])
            input_layers=[(colors['window'],alpha('inputOpacity'))]
            surface_layers=[(colors['window'],alpha('surfaceOpacity'))]
            states=[json.loads(raw) for raw in re.findall(r'SDDM_GEOMETRY (\{[^\n]+\})',log)]
            assert len(states)==6, 'Missing geometry evidence'
            sampling=[]
            with Image.open(destination/'background.png') as background:
                for state in states:
                    samples={}
                    for name,box in state['regions'].items():
                        if name == 'loginPanel': continue  # Layout-only Item, no painted surface.
                        if name in ('clockTime','calendarDate'):
                            layers=[]; roles={'text':(colors['text'],4.5)}
                        elif name in ('password','username'):
                            layers=input_layers
                            roles={'text':(colors['text'],4.5),'placeholder':(colors['secondary'],4.5),'focus':(colors['accent'],3)}
                        elif name in ('userList','sessionList'):
                            layers=surface_layers; roles={'text':(colors['text'],4.5),'focus':(colors['accent'],3)}
                        else:
                            error=name == 'loginError'
                            foreground=colors['negative' if error else 'selectedText']
                            layers=[(colors['window' if error else 'text'],alpha('errorOutlineOpacity' if error else 'bodyOutlineOpacity'))]
                            roles={'text':(foreground,4.5)}
                            # Preserve the failing raw ratio; the outline is the accepted local backdrop.
                            samples[name+'_without_outline']=sample_region(background,box,scale,[],
                                {'text':(foreground,4.5)},(width,height))
                        sample=sample_region(background,box,scale,layers,roles,(width,height))
                        assert_sample(sample); samples[name]=sample
                        if name in ('sessionSelection','keyboardLayout','shutdownButton','rebootButton','usernameDisplay'):
                            focus=sample_region(background,box,scale,surface_layers,{'border':(colors['accent'],3)},(width,height))
                            assert_sample(focus); samples[name+'_focus']=focus
                    sampling.append(dict(state=state['state'],regions=samples))
                # At rest the empty container margin must exactly reveal the wallpaper.
                from PIL import ImageChops
                normal=next(state for state in states if state['state']=='single-user')
                x,y,w,h=normal['regions']['loginPanel']
                margin=(round((x+2)*scale),round((y+20)*scale),round((x+12)*scale),round((y+h-20)*scale))
                with Image.open(destination/'single-user.png') as frame:
                    assert ImageChops.difference(frame.convert('RGB').crop(margin),background.convert('RGB').crop(margin)).getbbox() is None, 'Login container still paints a surface'
            (destination/'contrast.json').write_text(json.dumps(sampling,indent=2)+'\n')
            matrix.append(dict(layout_pixels=[width,height],scale=scale,capture_pixels=capture_size,
                               logical_surface=[width/scale,height/scale],checks=checks,exit_code=result.returncode,
                               container_margin_matches_wallpaper=True))
        report=dict(greeter_test_mode_loaded=True,ui_mock_matrix=matrix,authentication_tested=False,
                    actual_power_actions_tested=False,screenshot_kind='native offscreen Qt with mock SDDM models',
                    keyboard_events='QtTest keyClick; real QKeyEvent dispatch',
                    screenshot_capture='QQuickItem grabToImage; logical QSize/DPR rounding recorded; no postprocessing')
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))


if __name__=='__main__':
    main()
