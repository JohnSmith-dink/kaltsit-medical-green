"""Command and filesystem contract checks; deliberately no real transcoding."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EncodeWallpaperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.input = self.root / 'input with space.mp4'
        self.input.write_bytes(b'not a real video')
        self.log = self.root / 'args.json'
        self.env = dict(os.environ, PATH=str(self.bin), FAKE_ARGS=str(self.log))
        (self.bin/'realpath').symlink_to(shutil.which('realpath'))
        self.fake = self.bin/'ffmpeg'
        self.fake.write_text(f'#!{sys.executable}\nimport json, os, sys\n'
                             'json.dump({"args": sys.argv[1:], "report": os.getenv("FFREPORT")}, open(os.environ["FAKE_ARGS"], "w"))\n')
        self.fake.chmod(0o755)

    def run_script(self, *args):
        return subprocess.run([shutil.which('bash'), str(ROOT/'scripts/encode-wallpaper.sh'), *map(str,args)],
                              env=self.env, cwd=self.root, capture_output=True, text=True)

    def arguments(self):
        return json.loads(self.log.read_text())['args']

    def test_defaults_and_no_network_protocols(self):
        r=self.run_script(self.input)
        self.assertEqual(r.returncode,0,r.stderr)
        args=self.arguments()
        for flag,value in [('-r','30'),('-c:v','libx264'),('-pix_fmt','yuv420p'),('-maxrate','6M'),
                           ('-bufsize','6M'),('-movflags','+faststart'),('-protocol_whitelist','file'),('-fps_mode','cfr')]:
            self.assertEqual(args[args.index(flag)+1],value)
        self.assertIn('-an',args)
        self.assertIn('-n',args)
        self.assertNotIn('-y',args)
        self.assertEqual(args[-1],str(self.root/'input with space-wallpaper.mp4'))
        self.assertEqual(args[args.index('-vf')+1],"scale=w='min(1920,iw)':h=ih:force_original_aspect_ratio=decrease:force_divisible_by=2")

    def test_overrides_and_report_is_disabled(self):
        self.env['FFREPORT']='file=/outside/report.log'
        r=self.run_script('--fps','24','--width','1280','--bitrate','3500k',self.input,self.root/'out.mp4')
        self.assertEqual(r.returncode,0,r.stderr)
        args=self.arguments()
        self.assertEqual(args[args.index('-r')+1],'24')
        self.assertEqual(args[args.index('-maxrate')+1],'3500k')
        self.assertIn('min(1280,iw)',args[args.index('-vf')+1])
        self.assertIsNone(json.loads(self.log.read_text())['report'])

    def test_existing_output_and_input_are_preserved(self):
        out=self.root/'out.mp4'; out.write_bytes(b'keep')
        for target in (out,self.input):
            r=self.run_script(self.input,target)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('already exists',r.stderr)
        self.assertEqual(out.read_bytes(),b'keep')
        self.assertEqual(self.input.read_bytes(),b'not a real video')
        self.assertFalse(self.log.exists())

    def test_dangling_output_symlink_is_rejected(self):
        out=self.root/'link.mp4'; out.symlink_to(self.root/'absent.mp4')
        r=self.run_script(self.input,out)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.log.exists())
        self.assertFalse(out.exists())
        self.assertTrue(out.is_symlink())

    def test_output_directory_escape_and_symlink_escape(self):
        outside=self.root/'outside'; outside.mkdir()
        alias=self.root/'alias'; alias.symlink_to(outside,target_is_directory=True)
        for target in (outside/'out.mp4',alias/'out.mp4'):
            r=self.run_script(self.input,target)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('real input directory',r.stderr)
        self.assertFalse(self.log.exists())

    def test_input_symlink_uses_real_directory(self):
        sub=self.root/'sub'; sub.mkdir()
        link=sub/'link.mp4'; link.symlink_to(self.input)
        r=self.run_script(link)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(self.arguments()[-1],str(self.root/'input with space-wallpaper.mp4'))

    def test_missing_ffmpeg_is_clear(self):
        self.fake.unlink()
        r=self.run_script(self.input)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('ffmpeg is missing',r.stderr)

    def test_invalid_options_and_remote_input(self):
        for values in [('--fps','0'),('--width','1'),('--bitrate','-1'),('--fps',),('--wat',),('https://example.invalid/a.mp4',)]:
            r=self.run_script(*values, *(() if values[-1].startswith('https:') or len(values)==1 else (self.input,)))
            self.assertNotEqual(r.returncode,0,values)
        self.assertFalse(self.log.exists())
