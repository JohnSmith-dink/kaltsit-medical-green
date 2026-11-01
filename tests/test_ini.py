"""Regression cases for real KConfig text and conflict-aware restoration."""
import os
from pathlib import Path
import tempfile
import unittest

import test_controller as fixtures

theme = fixtures.theme


class IniTests(unittest.TestCase):
    def test_raw_flags_locales_unicode_and_escaped_values(self):
        text = ('# 中文注释\r\n[Group][Nested][$i]\r\n'
                'Name[zh_CN]=医疗白绿\r\nPath[$e]=$HOME/a=b\\s目录\r\n'
                'Empty=\r\nRemoved[$d]=\r\nLiteral=abc#def;ghi=jk\r\n')
        entries = theme.ini_entries(text)
        self.assertEqual(entries[('[Group][Nested][$i]', 'Name[zh_CN]')], '医疗白绿')
        self.assertEqual(entries[('[Group][Nested][$i]', 'Path[$e]')], '$HOME/a=b\\s目录')
        self.assertEqual(entries[('[Group][Nested][$i]', 'Empty')], '')
        self.assertIn(('[Group][Nested][$i]', 'Removed[$d]'), entries)
        self.assertEqual(entries[('[Group][Nested][$i]', 'Literal')], 'abc#def;ghi=jk')
        self.assertEqual(theme.edit_ini(text, {}), text)

    def test_edit_crlf_retains_comments_locales_and_missing_final_newline(self):
        text = '# 中文\r\n[General]\r\nName[zh_CN]=原名\r\nColorScheme=Before'
        expected = '# 中文\r\n[General]\r\nName[zh_CN]=原名\r\nColorScheme=After'
        self.assertEqual(theme.edit_ini(text, {('[General]', 'ColorScheme'): 'After'}), expected)
        appended = theme.edit_ini(text, {('[General]', 'New'): 'one=two'})
        self.assertTrue(appended.endswith('ColorScheme=Before\r\nNew=one=two\r\n'))
        self.assertNotIn('\n', appended.replace('\r\n', ''))

    def test_repeated_group_duplicate_update_and_delete(self):
        text = '[A]\nKey=one\n# retain\n[B]\nKey=other\n[A]\nKey=two\nExtra=x\n'
        self.assertEqual(theme.ini_entries(text)[('[A]', 'Key')], 'two')
        updated = theme.edit_ini(text, {('[A]', 'Key'): 'three'})
        self.assertEqual(theme.ini_entries(updated)[('[A]', 'Key')], 'three')
        self.assertEqual(updated.count('Key=three'), 1)
        deleted = theme.edit_ini(text, {('[A]', 'Key'): None, ('[Missing]', 'Gone'): None})
        self.assertNotIn(('[A]', 'Key'), theme.ini_entries(deleted))
        self.assertIn('# retain\n[B]\nKey=other\n[A]\nExtra=x\n', deleted)
        self.assertNotIn('[Missing]', deleted)

    def test_mixed_endings_unrelated_bytes_and_file_mode_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'kdeglobals'
            original = b'# old \xff\r\n[General]\nColorScheme=Before\r\nOther=x'
            path.write_bytes(original)
            os.chmod(path, 0o640)
            text = theme.read_text(path)
            theme.atomic_text(path, theme.edit_ini(text, {('[General]', 'ColorScheme'): 'After'}))
            self.assertEqual(path.read_bytes(), original.replace(b'Before', b'After'))
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)


class RestoreTextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ControllerTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.controller = self.fixture.controller

    def test_unchanged_apply_restore_preserves_exact_original_bytes(self):
        original = b'# comment\r\n[General]\r\nColorScheme=Old\r\nColorScheme=BreezeLight'
        self.fixture.config.mkdir()
        path = self.fixture.config / 'kdeglobals'
        path.write_bytes(original)
        self.controller.apply()
        self.controller.restore()
        self.assertEqual(path.read_bytes(), original)

    def test_legacy_and_current_restore_keep_later_edits_and_comments(self):
        for version in (1, 2, 3):
            with self.subTest(version=version):
                before = '# user\r\n[General]\r\nColorScheme=Old\r\nName[zh_CN]=原名\r\n'
                after = before.replace('ColorScheme=Old', 'ColorScheme=KaltsitMedicalGreen')
                current = after + '; later\r\nBrowserApplication=browser.desktop\r\n'
                self.fixture.put('kdeglobals', current)
                self.assertEqual(self.controller.restore_files({
                    'version': version, 'before': {'kdeglobals': before}, 'after': {'kdeglobals': after},
                }), [])
                self.assertEqual(theme.read_text(self.fixture.config / 'kdeglobals'),
                                 before + '; later\r\nBrowserApplication=browser.desktop\r\n')

    def test_conflicting_value_survives_and_is_reported(self):
        before = '[General]\nColorScheme=Old\n'
        after = '[General]\nColorScheme=Theme\n'
        current = '[General]\nColorScheme=UserChoice\n# later\n'
        self.fixture.put('kdeglobals', current)
        warnings = self.controller.restore_files({'before': {'kdeglobals': before},
                                                  'after': {'kdeglobals': after}})
        self.assertEqual(len(warnings), 1)
        self.assertIn('ColorScheme', warnings[0])
        self.assertEqual(theme.read_text(self.fixture.config / 'kdeglobals'), current)

    def test_gtk_unowned_exports_are_not_replaced_by_original_snapshot(self):
        before = '[Settings]\ngtk-theme-name=Old\ngtk-font-name=Old Font\n'
        after = '[Settings]\ngtk-theme-name=Breeze\ngtk-font-name=New Font\n'
        self.fixture.put('gtk-3.0/settings.ini', after)
        self.controller.restore_files({'before': {'gtk-3.0/settings.ini': before},
                                       'after': {'gtk-3.0/settings.ini': after}})
        self.assertEqual(theme.read_text(self.fixture.config / 'gtk-3.0/settings.ini'),
                         before.replace('Old Font', 'New Font'))
