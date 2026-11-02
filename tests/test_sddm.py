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
from test_assets import contrast, luminance, read_ini

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sddm_palette',ROOT/'sddm/build-palette.py')
palette_module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(palette_module)


def sample_region(image, logical_box, scale, layers, foregrounds, frame_size):
    """Sample every distinct RGB value, preserving the worst contrast, not an average."""
    import math
    box = [math.floor(logical_box[0]*scale), math.floor(logical_box[1]*scale),
           math.ceil((logical_box[0]+logical_box[2])*scale),
           math.ceil((logical_box[1]+logical_box[3])*scale)]
    pixels = set(image.crop(box).convert('RGB').get_flattened_data())
    def hex_rgb(pixel): return '#' + ''.join(f'{value:02x}' for value in pixel)
    def compose(pixel):
        for color, alpha in layers:
            top = [int(color[i:i+2],16) for i in (1,3,5)]
            pixel = tuple(round(alpha*c+(1-alpha)*b) for c,b in zip(top,pixel))
        return hex_rgb(pixel)
    lum = {p:luminance(hex_rgb(p)) for p in pixels}
    darkest, lightest = min(pixels,key=lum.get), max(pixels,key=lum.get)
    composites = {p:compose(p) for p in pixels}
    results = {}
    for role, values in foregrounds.items():
        color, threshold = values[:2]
        opacity = values[2] if len(values) == 3 else 1
        def ratio_on(background):
            fg=[int(color[i:i+2],16) for i in (1,3,5)]
            bg=[int(background[i:i+2],16) for i in (1,3,5)]
            composed=hex_rgb(tuple(round(opacity*f+(1-opacity)*b) for f,b in zip(fg,bg)))
            return contrast(composed,background)
        worst = min(pixels,key=lambda p:ratio_on(composites[p]))
        ratio = ratio_on(composites[worst])
        results[role] = dict(ratio=round(ratio,6), required=threshold,
                             source_rgb=hex_rgb(worst), composite_rgb=composites[worst],
                             foreground_opacity=opacity,
                             darkest_pixel_ratio=round(ratio_on(composites[darkest]),6),
                             lightest_pixel_ratio=round(ratio_on(composites[lightest]),6))
    # Image.PreserveAspectCrop uses centered uniform scaling of the existing still.
    factor = max(frame_size[0]/3840, frame_size[1]/2160)
    offset = [(3840*factor-frame_size[0])/2, (2160*factor-frame_size[1])/2]
    source_box = [(box[i]+offset[i%2])/factor for i in range(4)]
    return dict(logical_box=logical_box, physical_box=box, source_box=source_box,
                darkest=dict(rgb=hex_rgb(darkest), luminance=round(lum[darkest],6)),
                lightest=dict(rgb=hex_rgb(lightest), luminance=round(lum[lightest],6)),
                layers=layers, contrast=results)


def assert_sample(sample):
    for role, result in sample['contrast'].items():
        assert result['ratio'] >= result['required'], (role, sample)


def qml_number(name):
    match=re.search(r'readonly property real '+re.escape(name)+r':\s*([0-9.]+)',
                    (ROOT/'sddm/Main.qml').read_text())
    if not match: raise AssertionError('Missing SDDM geometry/alpha constant: '+name)
    return float(match[1])


class SddmTests(unittest.TestCase):
    def test_optical_alignment_check_accepts_ink_and_rejects_drift(self):
        from PIL import Image, ImageDraw
        from check_sddm_alignment import check
        background=Image.new('RGB',(1280,800),'white')
        frame=background.copy();draw=ImageDraw.Draw(frame)
        for top in (72,153,370,432,490):draw.rectangle((72,top,90,top+6),fill='black')
        self.assertTrue(all(row['passed'] for row in check(frame,background)))
        shifted=Image.new('RGB',frame.size,'white');shifted.paste(frame,(5,0))
        self.assertFalse(any(row['passed'] for row in check(shifted,background)))

    def test_optical_alignment_check_rejects_missing_ink_and_size_mismatch(self):
        from PIL import Image
        from check_sddm_alignment import check
        background=Image.new('RGB',(1280,800),'white')
        self.assertFalse(any(row['passed'] for row in check(background,background)))
        with self.assertRaisesRegex(ValueError,'Size mismatch'):
            check(Image.new('RGB',(1280,801)),background)

    def test_vm_preview_hashes_and_provenance(self):
        manifest=json.loads((ROOT/'previews/manifest.json').read_text())
        captures=[item for item in manifest['screenshots'] if item['file'].startswith('sddm/')]
        self.assertEqual({item['file'] for item in captures},{
            'sddm/login.png','sddm/wrong-password.png',
            'sddm/login-v2.png','sddm/login-v2-error.png',
            'sddm/login-v3.png','sddm/login-v3-error.png','sddm/login-v3-multiuser.png',
            'sddm/login-v5.png','sddm/login-v5-error.png','sddm/login-v5-multiuser.png',
            'sddm/login-v6.png','sddm/login-v6-error.png','sddm/login-v6-long-session.png',
            'sddm/login-v6-nofont.png','sddm/login-v6-multiuser.png',
        })
        for item in captures:
            with self.subTest(file=item['file']):
                path=ROOT/'previews'/item['file']
                self.assertTrue(path.is_file(),str(path))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])
                self.assertEqual(item['pixels'],[1280,800])
                self.assertEqual(item['kind'],'SDDM screenshot in isolated NixOS VM')
                self.assertFalse(item['physical_desktop_acceptance'])
                if item['file'].startswith(('sddm/login-v2','sddm/login-v3','sddm/login-v5','sddm/login-v6')):
                    self.assertEqual(item['development_layout'],re.search(r'login-(v\d+)',item['file'])[1])
                    self.assertEqual(item['release_status'],'Unreleased')
                    self.assertEqual(item['sddm_authentication_performed'],item['file'] != 'sddm/login-v6-nofont.png')
                    self.assertEqual(item['image_processing'],'none; original QEMU screenshot bytes')
                    self.assertRegex(item['runtime_source_commit'],r'^[0-9a-f]{40}$')
                if item['file'].startswith('sddm/login-v6'):
                    self.assertFalse(item['font_binary_distributed'])
                    self.assertEqual(item['font_family'], 'system fallback' if item['file'].endswith('nofont.png') else 'OPPO Sans 4.0')
                    if item['font_family'] != 'system fallback':
                        self.assertRegex(item['local_font_sha256'],r'^[0-9a-f]{64}$')

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
        from PIL import Image, ImageOps
        colors=palette_module.palette(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        input_alpha=qml_number('inputOpacity')
        surface_alpha=qml_number('surfaceOpacity')
        left, width=qml_number('leftInset'),qml_number('panelWidth')
        self.assertEqual((left,width),(72,288))
        with Image.open(ROOT/'share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg') as source:
            for w,h,scale in ((1280,800,1),(1920,1080,1),(3120,2080,1.75)):
                frame=ImageOps.fit(source.convert('RGB'),(w,h),method=Image.Resampling.BILINEAR)
                top=round(h/scale*.451)
                # Conservative envelope includes upward sessions, downward users and errors.
                box=[left,200 if h==800 else top-148,width,top+372-(200 if h==800 else top-148)]
                with self.subTest(layout=(w,h,scale)):
                    assert_sample(sample_region(frame,box,scale,[(colors['view'],input_alpha)],
                        {'text':(colors['text'],4.5),'placeholder':(colors['secondary'],4.5),
                         'error_border':(colors['negative'],3),'focus':(colors['accent'],3)},(w,h)))
                    assert_sample(sample_region(frame,box,scale,[(colors['window'],surface_alpha)],
                        {'list_text':(colors['text'],4.5),'focus':(colors['accent'],3)},(w,h)))
                    for foreground, outline, alpha in (
                        ('selectedText','text',qml_number('bodyOutlineOpacity')),
                        ('negative','window',qml_number('errorOutlineOpacity')),
                    ):
                        assert_sample(sample_region(frame,box,scale,[(colors[outline],alpha)],
                            {foreground:(colors[foreground],4.5)},(w,h)))
                    assert_sample(sample_region(frame,box,scale,[(colors['text'],qml_number('bodyOutlineOpacity'))],
                        {'label':(colors['view'],4.5,qml_number('labelOpacity')),
                         'focus':(colors['selectedText'],3,qml_number('focusOpacity'))},(w,h)))
        self.assertGreaterEqual(contrast(colors['selectedText'],colors['accent']),4.5)

    def test_outlines_and_input_against_extreme_underlays(self):
        from PIL import Image
        colors=palette_module.palette(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        # Removing the parent surface must not silently invalidate placeholder contrast.
        for backdrop in ('#000000','#ffffff'):
            frame=Image.new('RGB',(1,1),backdrop)
            for foreground, layer, alpha, required in (
                ('selectedText','text',qml_number('bodyOutlineOpacity'),4.5),
                ('negative','window',qml_number('errorOutlineOpacity'),4.5),
                ('secondary','view',qml_number('inputOpacity'),4.5),
                ('text','view',qml_number('inputOpacity'),4.5),
                ('accent','view',qml_number('inputOpacity'),3),
                ('accent','window',qml_number('surfaceOpacity'),3),
            ):
                with self.subTest(backdrop=backdrop,foreground=foreground,alpha=alpha):
                    assert_sample(sample_region(frame,[0,0,1,1],1,[(colors[layer],alpha)],
                        {foreground:(colors[foreground],required)},(1,1)))

    def test_clock_and_date_on_sampled_wallpaper(self):
        from PIL import Image, ImageOps
        colors=palette_module.palette(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        with Image.open(ROOT/'share/wallpapers/KaltsitMedicalGreen/contents/images/3840x2160.jpg') as source:
            for w,h,scale in ((1280,800,1),(1920,1080,1),(3120,2080,1.75)):
                frame=ImageOps.fit(source.convert('RGB'),(w,h),method=Image.Resampling.BILINEAR)
                for label,box in [('clock',[72,71.75,200,58]),('date',[72,152.25,210,22])]:
                    with self.subTest(layout=(w,h,scale),element=label):
                        assert_sample(sample_region(frame,box,scale,[],{label:(colors['text'],4.5)},(w,h)))

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
