"""Safe package updates and native power routes in the desktop confirmation."""
import difflib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_assets import contrast, read_ini

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


logout = load_module('readable_logout', 'scripts/readable-logout.py')
checks = load_module('check_logout', 'tests/check-logout-resources.py')


class LogoutRenderingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.workspace = root / 'workspace'
        self.upstream = self.workspace / 'share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout'
        self.upstream.mkdir(parents=True)
        self.original = '/* KDE */\nItem {\n    property string layout: "before"\n    signal rebootRequested()\n}\n'
        (self.upstream/'Logout.qml').write_text(self.original)
        (self.upstream/'timer.js').write_bytes(b'// upstream timer\r\n')
        assets = root/'assets'
        assets.mkdir()
        self.changed = self.original.replace('"before"', '"after"')
        (assets/'layout.patch').write_text(''.join(difflib.unified_diff(self.original.splitlines(True),
            self.changed.splitlines(True), 'a/Logout.qml', 'b/Logout.qml')))
        (assets/'LeftConfirmation.qml').write_text('Item {}\n')
        shutil.copyfile(ROOT/'logout/LockBackdrop.qml', assets/'LockBackdrop.qml')
        replacement = patch.object(logout, 'ASSETS', assets)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.output = root/'out'
        (self.output/'share/doc/kaltsit-theme').mkdir(parents=True)
        (self.output/logout.LOCK).mkdir(parents=True)
        for name in ('MedicalClock.qml', 'MedicalPalette.js'):
            (self.output/logout.LOCK/name).write_text('same resource '+name+'\n')
        self.wallpaper = self.output/logout.WALLPAPER
        self.wallpaper.parent.mkdir(parents=True)
        self.wallpaper.write_bytes(b'\xff\xd8wallpaper fixture\xff\xd9')

    def test_install_preserves_readonly_upstream_and_stages_shared_resources(self):
        self.upstream.chmod(0o555)
        logout.install(self.workspace, self.output, 'test')
        dest = self.output/logout.THEME
        self.assertEqual((dest/'Logout.qml').read_text(), self.changed)
        self.assertEqual((self.upstream/'Logout.qml').read_text(), self.original)
        self.assertEqual((dest/'timer.js').read_bytes(), (self.upstream/'timer.js').read_bytes())
        self.assertTrue((dest/'LeftConfirmation.qml').exists())
        self.assertEqual((dest/'LockBackdrop.qml').read_bytes(), (ROOT/'logout/LockBackdrop.qml').read_bytes())
        self.assertEqual((dest/'LockWallpaper.jpg').read_bytes(), self.wallpaper.read_bytes())
        record = json.loads((self.output/'share/doc/kaltsit-theme/logout-rendering.json').read_text())
        self.assertEqual(record['fullscreen_background'], '锁屏壁纸（主题自带图，原亮度）')
        for name in ('MedicalClock.qml', 'MedicalPalette.js'):
            self.assertEqual((dest/name).read_bytes(), (self.output/logout.LOCK/name).read_bytes())

    def test_changed_kde_layout_fails_without_publishing_a_partial_confirmation(self):
        (self.upstream/'Logout.qml').write_text('Item { signal logoutRequested() }\n')
        with self.assertRaisesRegex(ValueError, 'review required'):
            logout.install(self.workspace, self.output, 'test')
        self.assertFalse((self.output/logout.THEME).exists())

    def test_verifier_detects_a_misrouted_power_button(self):
        prefix = 'Item {\n    signal rebootRequested()\n    Timer { onTriggered: remainingTime-- }\n'
        mouse = '    MouseArea {\n        onClicked: root.cancelRequested()\n    }\n'
        buttons = '            LogoutButton {\n                onClicked: root.rebootRequested()\n            }\n        }\n}\n'
        old = prefix + '    Rectangle {\n        id: backgroundRect\n    }\n' + mouse + '    UserDelegate {}\n    ColumnLayout {\n' + buttons
        backdrop = '    LockBackdrop {\n        anchors.fill: parent\n    }\n'
        new = prefix + backdrop + mouse + '    LeftConfirmation {\n' + buttons
        checks.check_handlers(old, new)
        with self.assertRaises(AssertionError):
            checks.check_handlers(old, new.replace('onClicked: root.rebootRequested()', 'onClicked: root.haltRequested()'))
        with self.assertRaises(AssertionError):
            checks.check_handlers(old, new.replace(backdrop + mouse, mouse + backdrop))

    def test_missing_bundled_wallpaper_leaves_no_partial_confirmation(self):
        self.wallpaper.unlink()
        with self.assertRaises(FileNotFoundError):
            logout.install(self.workspace, self.output, 'test')
        self.assertFalse((self.output/logout.THEME).exists())

    def test_backdrop_is_an_untinted_synchronous_copy_of_the_lock_image(self):
        source = (ROOT/'logout/LockBackdrop.qml').read_text()
        # Only a solid fallback and its Image may be drawn; extra layers change the wallpaper.
        self.assertEqual(re.findall(r'^\s*(\w+)\s*\{', source, re.MULTILINE), ['Rectangle', 'Image'])
        image = source.split('    Image {', 1)[1]
        self.assertIn('color: "#17291F"', source.split('    Image {', 1)[0])
        for prop in ('anchors.fill: parent', 'source: "LockWallpaper.jpg"', 'fillMode: Image.PreserveAspectCrop',
                     'autoTransform: true', 'asynchronous: false'):
            self.assertIn(prop, image)
        self.assertRegex(image, r'onStatusChanged:.*Image\.Error.*console\.warn\(')
        self.assertNotRegex(source, r'(?i)\b(opacity|layer|tint|gradient|blur|shadereffect)\b')

    def test_outlined_text_icon_and_focus_contrast(self):
        palette = read_ini(ROOT/'share/color-schemes/KaltsitMedicalGreen.colors')
        text = list(map(int, palette['Colors:View']['ForegroundNormal'].split(',')))
        ink = palette['Colors:Selection']['ForegroundNormal']
        accent = palette['Colors:Button']['DecorationFocus']
        self.assertGreaterEqual(contrast(ink, accent), 3.0)  # icon on its green disc
        for backing in (0, 128, 255):
            outline = ','.join(str(round(c*0.85 + backing*0.15)) for c in text)
            with self.subTest(backing=backing):
                self.assertGreaterEqual(contrast(ink, outline), 4.5)  # text and focus ring
