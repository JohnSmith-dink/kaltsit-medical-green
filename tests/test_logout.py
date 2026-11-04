"""Safe package updates and native power routes in the desktop confirmation."""
import difflib
import importlib.util
from pathlib import Path
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
        replacement = patch.object(logout, 'ASSETS', assets)
        replacement.start()
        self.addCleanup(replacement.stop)
        self.output = root/'out'
        (self.output/'share/doc/kaltsit-theme').mkdir(parents=True)
        (self.output/logout.LOCK).mkdir(parents=True)
        for name in ('MedicalClock.qml', 'MedicalPalette.js'):
            (self.output/logout.LOCK/name).write_text('same resource '+name+'\n')

    def test_install_preserves_readonly_upstream_and_stages_shared_resources(self):
        self.upstream.chmod(0o555)
        logout.install(self.workspace, self.output, 'test')
        dest = self.output/logout.THEME
        self.assertEqual((dest/'Logout.qml').read_text(), self.changed)
        self.assertEqual((self.upstream/'Logout.qml').read_text(), self.original)
        self.assertEqual((dest/'timer.js').read_bytes(), (self.upstream/'timer.js').read_bytes())
        self.assertTrue((dest/'LeftConfirmation.qml').exists())
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
        new = prefix + mouse + '    LeftConfirmation {\n' + buttons
        checks.check_handlers(old, new)
        with self.assertRaises(AssertionError):
            checks.check_handlers(old, new.replace('onClicked: root.rebootRequested()', 'onClicked: root.haltRequested()'))

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
