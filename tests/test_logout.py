"""Logout rendering must preserve power controls and remain legible."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from test_assets import contrast, read_ini


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("readable_logout", ROOT / "scripts/readable-logout.py")
logout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logout)


class LogoutRenderingTests(unittest.TestCase):
    def test_only_background_changes_and_support_files_are_preserved(self):
        prefix = '/* SPDX-License-Identifier: GPL-2.0-or-later */\nItem {\n signal rebootRequested()\n Rectangle {\n'
        suffix = '\n }\n Timer { onTriggered: remainingTime-- }\n}\n'
        source = prefix + logout.UPSTREAM_BACKGROUND + suffix
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "workspace/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout"
            upstream.mkdir(parents=True)
            (upstream / "Logout.qml").write_text(source)
            for name in ("LogoutButton.qml", "timer.js"):
                (upstream / name).write_bytes(b"// upstream content, kept byte-for-byte\r\n")
            output = root / "out"
            (output / "share/doc/kaltsit-theme").mkdir(parents=True)
            logout.install(root / "workspace", output, "test-version")
            target = output / "share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout"
            self.assertEqual((target / "Logout.qml").read_text(), prefix + logout.PALETTE_BACKGROUND + suffix)
            for name in ("LogoutButton.qml", "timer.js"):
                self.assertEqual((target / name).read_bytes(), (upstream / name).read_bytes())
            self.assertEqual((upstream / "Logout.qml").read_text(), source)

    def test_upstream_changes_require_review(self):
        for changed in ("", logout.UPSTREAM_BACKGROUND.replace("0.85", "0.9"),
                        logout.UPSTREAM_BACKGROUND * 2):
            with self.subTest(source=changed):
                with self.assertRaisesRegex(ValueError, "review required"):
                    logout.render_logout(changed)

    def test_normal_and_unfocused_text_contrast_over_extreme_backdrops(self):
        palette = read_ini(ROOT / "share/color-schemes/KaltsitMedicalGreen.colors")["Colors:Complementary"]
        background = list(map(int, palette["BackgroundNormal"].split(",")))
        foreground = list(map(int, palette["ForegroundNormal"].split(",")))
        opacity = float(logout.PALETTE_BACKGROUND.rsplit("opacity:", 1)[1])
        for backdrop in (0, 255):
            surface = [round(opacity * c + (1 - opacity) * backdrop) for c in background]
            # Breeze LogoutButton uses 0.75 opacity when not focused/hovered.
            for text_alpha in (1.0, 0.75):
                text = [round(text_alpha * c + (1 - text_alpha) * b)
                        for c, b in zip(foreground, surface)]
                ratio = contrast(",".join(map(str, text)), ",".join(map(str, surface)))
                with self.subTest(backdrop=backdrop, text_alpha=text_alpha):
                    self.assertGreaterEqual(ratio, 4.5)
