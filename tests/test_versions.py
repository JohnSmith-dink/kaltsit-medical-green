"""All version-bearing distribution entries must match the latest release."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
METADATA = [
    'share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/metadata.json',
    'share/plasma/desktoptheme/KaltsitMedicalGreen/metadata.json',
    'share/plasma/wallpapers/org.xinyan.kaltsit.medicalgreen.lock/metadata.json',
    'motion/wallpaper/metadata.json',
]


class VersionTests(unittest.TestCase):
    def read(self, name):
        path = ROOT/name
        self.assertTrue(path.is_file(), f'Required version file is missing: {name}')
        return path.read_text(encoding='utf-8')

    def extract(self, name, pattern, field):
        match = re.search(pattern, self.read(name), re.MULTILINE)
        self.assertIsNotNone(match, f'{name}: missing or invalid {field}')
        return match[1]

    def setUp(self):
        self.released = self.extract('CHANGELOG.md', r'^## v?(\d+\.\d+\.\d+)(?:\s|$)', 'released version heading (Unreleased is excluded)')

    def test_nix_packages_match_latest_release(self):
        for name in ('package.nix', 'motion.nix'):
            with self.subTest(file=name):
                value=self.extract(name, r'^\s*version\s*=\s*"([^"]+)";', 'version')
                self.assertEqual(value,self.released,f'{name}: version differs from CHANGELOG latest release')

    def test_controller_matches_latest_release(self):
        value=self.extract('tools/kaltsit_theme.py',r'^VERSION\s*=\s*"([^"]+)"','VERSION')
        self.assertEqual(value,self.released,'Controller VERSION differs from CHANGELOG latest release')

    def test_four_versioned_metadata_files_match_latest_release(self):
        for name in METADATA:
            with self.subTest(file=name):
                try:
                    metadata=json.loads(self.read(name))
                except json.JSONDecodeError as error:
                    self.fail(f'{name}: invalid JSON: {error}')
                self.assertIn('KPlugin',metadata,f'{name}: missing KPlugin')
                self.assertIn('Version',metadata['KPlugin'],f'{name}: missing KPlugin.Version')
                self.assertEqual(metadata['KPlugin']['Version'],self.released,f'{name}: KPlugin.Version differs from CHANGELOG latest release')
