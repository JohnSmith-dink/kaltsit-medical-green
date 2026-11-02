"""Static SDDM contracts and generated-palette accessibility; no host login."""
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from test_assets import contrast, read_ini

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sddm_palette',ROOT/'sddm/build-palette.py')
palette_module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(palette_module)


class SddmTests(unittest.TestCase):
    def test_vm_preview_hashes_and_provenance(self):
        manifest=json.loads((ROOT/'previews/manifest.json').read_text())
        captures=[item for item in manifest['screenshots'] if item['file'].startswith('sddm/')]
        self.assertEqual({item['file'] for item in captures},{'sddm/login.png','sddm/wrong-password.png'})
        for item in captures:
            with self.subTest(file=item['file']):
                path=ROOT/'previews'/item['file']
                self.assertTrue(path.is_file(),str(path))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])
                self.assertEqual(item['pixels'],[1280,800])
                self.assertEqual(item['kind'],'SDDM screenshot in isolated NixOS VM')
                self.assertFalse(item['physical_desktop_acceptance'])

    def test_qt6_metadata_and_entrypoint(self):
        meta=read_ini(ROOT/'sddm/metadata.desktop')['SddmGreeterTheme']
        self.assertEqual(meta['QtVersion'],'6')
        self.assertEqual(meta['Theme-Id'],'KaltsitMedicalGreen')
        for field in ('MainScript','ConfigFile'):
            self.assertTrue((ROOT/'sddm'/meta[field]).is_file(),field)
        self.assertEqual(meta['Version'],'1.3.0')
        self.assertRegex((ROOT/'sddm.nix').read_text(),r'version = "'+re.escape(meta['Version'])+'";')

    def test_generated_palette_uses_only_existing_colors(self):
        path=ROOT/'share/color-schemes/KaltsitMedicalGreen.colors'
        colors=read_ini(path)
        expected={f'#{int(r):02x}{int(g):02x}{int(b):02x}' for section in colors.sections()
                  for value in colors[section].values() if re.fullmatch(r'\d+,\d+,\d+',value)
                  for r,g,b in [value.split(',')]}
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'Palette.js'
            r=subprocess.run([sys.executable,str(ROOT/'sddm/build-palette.py'),str(path),str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            entries=dict(re.findall(r'var (\w+) = "(#[0-9a-f]{6})";',out.read_text()))
        self.assertEqual(entries,palette_module.palette(path))
        self.assertTrue(set(entries.values())<=expected)
        self.assertNotRegex((ROOT/'sddm/Main.qml').read_text(),r'#[0-9a-fA-F]{3,8}')

    def test_error_text_and_control_boundaries_contrast(self):
        colors=palette_module.palette(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        for text in ('text','secondary','negative'):
            for background in ('window','view','alternate'):
                with self.subTest(text=text,background=background):
                    self.assertGreaterEqual(contrast(colors[text],colors[background]),4.5)
        self.assertGreaterEqual(contrast(colors['selectedText'],colors['selected']),4.5)
        for boundary in ('secondary','accent','hover','selected'):
            for background in ('window','view','alternate'):
                with self.subTest(boundary=boundary,background=background):
                    self.assertGreaterEqual(contrast(colors[boundary],colors[background]),3)

    def test_translucent_controls_contrast_after_compositing(self):
        colors=palette_module.palette(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        source=(ROOT/'sddm/Main.qml').read_text()
        match=re.search(r'readonly property real surfaceOpacity:\s*([0-9.]+)',source)
        self.assertIsNotNone(match,'SDDM backplate opacity must be explicit for contrast validation')
        alpha=float(match[1])
        self.assertGreater(alpha,0)
        self.assertLessEqual(alpha,1)
        plate=[int(colors['window'][i:i+2],16) for i in (1,3,5)]
        # Black is the minimum luminance behind this white backplate; also
        # check white and intermediate grays, without averaging image pixels.
        for underlay in range(256):
            background='#'+''.join(f'{round(alpha*c+(1-alpha)*underlay):02x}' for c in plate)
            for foreground in ('text','secondary','negative'):
                with self.subTest(underlay=underlay,foreground=foreground):
                    self.assertGreaterEqual(contrast(colors[foreground],background),4.5)
            self.assertGreaterEqual(contrast(colors['accent'],background),3)
            self.assertGreaterEqual(contrast(colors['secondary'],background),3)
        # Circular primary-button focus ring and clock halo use existing white.
        self.assertGreaterEqual(contrast(colors['selectedText'],colors['selected']),4.5)
        self.assertGreaterEqual(contrast(colors['text'],colors['window']),4.5)

    def test_palette_missing_or_bad_source_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'incomplete.colors'
            path.write_text('[Colors:Window]\nBackgroundNormal=999,0,0\n')
            with self.assertRaises(ValueError): palette_module.palette(path)
            path.write_text('[Colors:Window]\nBackgroundNormal=255,255,255\n')
            with self.assertRaises(KeyError): palette_module.palette(path)

    def test_static_asset_and_independent_package(self):
        package=(ROOT/'sddm.nix').read_text()
        self.assertIn('./share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg',package)
        self.assertIn('license = lib.licenses.unfree',package)
        self.assertNotIn('sddm', (ROOT/'package.nix').read_text())
        self.assertNotIn('sddm', (ROOT/'home-manager.nix').read_text().lower())
        qml=(ROOT/'sddm/Main.qml').read_text()
        self.assertIn('Image.PreserveAspectCrop',qml)
        self.assertNotIn('QtMultimedia',qml)
        self.assertNotIn('org.kde',qml)
        self.assertNotIn('console.',qml)
        self.assertIn('TextInput.Password',qml)
        self.assertIn('password.clear()',qml)
