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


def fixture_sources():
    main = ('/* SPDX-License-Identifier: GPL-2.0-or-later */\nItem {\n'
            + logout.UPSTREAM_BACKGROUND + '    UserDelegate { name: kuser.fullName }\n'
            + ''.join(logout.UPSTREAM_LABEL + '            text: message\n        }\n' for _ in range(5))
            + ' Timer { onTriggered: remainingTime-- }\n signal rebootRequested()\n}\n')
    button = '/* upstream */\nActionButton {\n Keys.onPressed: cancelTimer()\n}\n'
    action = ('/* SPDX-License-Identifier: LGPL-2.0-or-later */\nItem {\n'
              + logout.UPSTREAM_BUTTON_SURFACE + '\n' + logout.UPSTREAM_BUTTON_TEXT
              + '\n Keys.onReturnPressed: clicked()\n}\n')
    user = 'Item {\n' + logout.UPSTREAM_USER_TEXT + '\n Keys.onSpacePressed: clicked()\n}\n'
    return main, button, action, user


class LogoutRenderingTests(unittest.TestCase):
    def test_only_visual_declarations_change(self):
        main, button, action, user = fixture_sources()
        rendered = logout.render_logout(main)
        self.assertNotIn('id: backgroundRect', rendered)
        self.assertEqual(rendered.replace(logout.OUTLINED_LABEL, logout.UPSTREAM_LABEL)
                         .replace('KaltsitLogoutUserDelegate', 'UserDelegate'),
                         main.replace(logout.UPSTREAM_BACKGROUND, ''))
        self.assertEqual(logout.render_button(button).replace('KaltsitLogoutActionButton', 'ActionButton'), button)
        self.assertEqual(logout.render_action(action).replace(logout.LOCAL_BUTTON_SURFACE, logout.UPSTREAM_BUTTON_SURFACE)
                         .replace(logout.LOCAL_BUTTON_TEXT, logout.UPSTREAM_BUTTON_TEXT), action)
        self.assertEqual(logout.render_user(user).replace(logout.LOCAL_USER_TEXT, logout.UPSTREAM_USER_TEXT), user)

    def test_install_preserves_timer_and_never_modifies_upstream(self):
        main, button, action, user = fixture_sources()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / 'workspace/share/plasma/look-and-feel/org.kde.breeze.desktop/contents/logout'
            components = root / 'workspace/lib/qt-6/qml/org/kde/breeze/components'
            upstream.mkdir(parents=True); components.mkdir(parents=True)
            sources = {upstream / 'Logout.qml': main, upstream / 'LogoutButton.qml': button,
                       components / 'ActionButton.qml': action, components / 'UserDelegate.qml': user}
            for path, value in sources.items():
                path.write_text(value)
            timer = b'// upstream timer\r\ncallbacks.forEach(c => c());\r\n'
            (upstream / 'timer.js').write_bytes(timer)
            upstream.chmod(0o555)
            output = root / 'out'
            (output / 'share/doc/kaltsit-theme').mkdir(parents=True)
            logout.install(root / 'workspace', output, 'test-version')
            target = output / 'share/plasma/look-and-feel/org.xinyan.kaltsit.medicalgreen/contents/logout'
            self.assertEqual((target / 'timer.js').read_bytes(), timer)
            self.assertEqual((target / 'Logout.qml').read_text(), logout.render_logout(main))
            self.assertTrue((target / 'KaltsitLogoutActionButton.qml').is_file())
            self.assertTrue((target / 'KaltsitLogoutUserDelegate.qml').is_file())
            for path, value in sources.items():
                self.assertEqual(path.read_text(), value)

    def test_upstream_changes_require_review(self):
        for function, source in zip((logout.render_logout, logout.render_button,
                                     logout.render_action, logout.render_user), fixture_sources()):
            for changed in ('', source + source):
                with self.subTest(function=function.__name__, source=changed):
                    with self.assertRaisesRegex(ValueError, 'review required'):
                        function(changed)
        with self.assertRaisesRegex(ValueError, 'review required'):
            logout.render_logout(fixture_sources()[0].replace('opacity: 0.85', 'opacity: 0.9'))

    def test_text_outlines_icons_and_focus_contrast(self):
        palette = read_ini(ROOT / 'share/color-schemes/KaltsitMedicalGreen.colors')['Colors:Complementary']
        colors = {key: list(map(int, palette[key].split(',')))
                  for key in ('BackgroundNormal', 'ForegroundNormal', 'DecorationFocus')}
        blend = lambda color, base, opacity: [round(opacity * c + (1 - opacity) * b)
                                             for c, b in zip(color, base)]
        ratio = lambda a, b: contrast(','.join(map(str, a)), ','.join(map(str, b)))
        for gray in (0, 128, 255):
            backdrop = [gray] * 3
            for opacity in (1.0, 0.75):
                with self.subTest(backdrop=gray, opacity=opacity):
                    # Text and its outline inherit the same button opacity.
                    foreground = blend(colors['ForegroundNormal'], backdrop, opacity)
                    halo = blend(colors['BackgroundNormal'], backdrop, opacity)
                    self.assertGreaterEqual(ratio(foreground, halo), 4.5)
                    disc = blend(colors['BackgroundNormal'], backdrop, 0.96 * opacity)
                    icon = blend(colors['ForegroundNormal'], disc, opacity)
                    self.assertGreaterEqual(ratio(icon, disc), 3.0)
            disc = blend(colors['BackgroundNormal'], backdrop, 0.96)
            focus = blend(colors['DecorationFocus'], backdrop, 0.96)
            self.assertGreaterEqual(ratio(focus, disc), 3.0)
