"""Component transactions are exercised only in temporary homes and a fake bus."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import unittest
from unittest import mock

import test_controller as baseline

theme = baseline.theme
ROOT = Path(__file__).resolve().parents[1]


class ComponentTests(unittest.TestCase):
    put = baseline.ControllerTests.put
    entries = baseline.ControllerTests.entries
    local_cursor = baseline.ControllerTests.local_cursor

    def setUp(self):
        baseline.ControllerTests.setUp(self)
        source = ROOT / "share/color-schemes/KaltsitMedicalGreen.colors"
        target = self.share / "color-schemes/KaltsitMedicalGreen.colors"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def tree(self):
        return {str(p.relative_to(self.home)): ("link", str(p.readlink())) if p.is_symlink()
                else ("file", p.read_bytes()) if p.is_file() else ("dir",)
                for p in self.home.rglob("*")}

    def managed(self, relative):
        path = self.config / relative
        target = self.home / ("managed-" + relative.replace("/", "-"))
        target.write_text("# Declarative configuration\n[Settings]\nKeep=untouched\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
        return path, target, target.read_bytes()

    def test_optional_managed_files_skip_and_survive_restore(self):
        for component, relative in (("cursor", "kcminputrc"), ("wallpaper", "plasma-org.kde.plasma.desktop-appletsrc"),
                                    ("lockscreen", "kscreenlockerrc"), ("gtk", "gtk-3.0/settings.ini"),
                                    ("ghostty", "ghostty/config"), ("konsole", "konsolerc")):
            with self.subTest(component=component):
                path, target, original = self.managed(relative)
                before_wallpapers = list(self.process.desktops)
                result = self.controller.apply()
                self.assertEqual(result["result"], "partially-applied")
                status = self.controller.status()["components"]
                self.assertEqual(status[component]["status"], "skipped")
                self.assertTrue(status[component]["reason"])
                self.assertEqual(status["core"]["status"], "applied")
                self.assertTrue(path.is_symlink())
                self.assertEqual(target.read_bytes(), original)
                if component == "wallpaper":
                    self.assertEqual(self.process.desktops, before_wallpapers)
                self.assertEqual(self.controller.restore()["result"], "restored")
                self.assertTrue(path.is_symlink())
                self.assertEqual(target.read_bytes(), original)
                path.unlink()

    def test_gtk4_or_css_link_skips_whole_gtk_component(self):
        for relative in ("gtk-4.0/settings.ini", "gtk-3.0/colors.css", "gtk-4.0/gtk.css"):
            with self.subTest(path=relative):
                path, target, old = self.managed(relative)
                self.controller.apply()
                self.assertEqual(self.controller.status()["components"]["gtk"]["status"], "skipped")
                self.assertEqual(target.read_bytes(), old)
                self.assertEqual(self.controller.restore()["result"], "restored")
                self.assertEqual(target.read_bytes(), old)
                path.unlink()

    def test_managed_parent_directory_is_not_followed_for_writes(self):
        target = self.home / "managed-ghostty-directory"
        target.mkdir()
        (target / "config").write_text("font-size = 14\n")
        self.config.mkdir(parents=True, exist_ok=True)
        (self.config / "ghostty").symlink_to(target, target_is_directory=True)
        self.controller.apply()
        self.assertEqual(self.controller.status()["components"]["ghostty"]["status"], "skipped")
        self.assertEqual((target / "config").read_text(), "font-size = 14\n")
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertTrue((self.config / "ghostty").is_symlink())

    def test_restore_retains_record_when_terminal_parent_becomes_managed(self):
        self.put("ghostty/config", "font-size = 14\n")
        self.controller.apply()
        original_dir = self.config / "ghostty"
        moved = self.home / "declarative-ghostty"
        original_dir.rename(moved)
        original_dir.symlink_to(moved, target_is_directory=True)
        contents = (moved / "config").read_bytes()
        result = self.controller.restore()
        self.assertEqual(result["result"], "restore-incomplete")
        self.assertEqual((moved / "config").read_bytes(), contents)
        self.assertTrue(original_dir.is_symlink())
        self.assertTrue(self.controller.state_file.exists())

    def test_newly_managed_gtk_on_restore_suppresses_indirect_writers(self):
        self.controller.apply()
        path = self.config / "gtk-3.0/settings.ini"
        target = self.home / "gtk-managed-after-apply"
        path.rename(target)
        path.symlink_to(target)
        original = target.read_bytes()
        start = len(self.process.calls)
        result = self.controller.restore()
        self.assertEqual(result["result"], "restore-incomplete")
        self.assertEqual(target.read_bytes(), original)
        self.assertTrue(path.is_symlink())
        self.assertTrue(self.controller.state_file.exists())
        calls = self.process.calls[start:]
        self.assertFalse(any(call[0].startswith("plasma-apply") for call in calls))
        self.assertFalse(any(call[0] == "busctl" and call[3] in {"/kdeglobals", "/kcminputrc", "/kwinrc"} for call in calls))

    def test_gtk_skip_same_id_cursor_reloads_without_gtk_notifications(self):
        self.local_cursor()
        self.put("kcminputrc", f"[Mouse]\ncursorTheme={theme.CURSOR}\ncursorSize=36\n")
        reloads = []
        real_refresh = self.backend.refresh_cursor

        def observe():
            reloads.append(self.entries("kcminputrc").get(("[Mouse]", "cursorTheme")))
            real_refresh()

        with mock.patch.object(self.backend, "refresh_cursor", side_effect=observe):
            self.controller.apply(skip=("gtk",))
            self.assertEqual(reloads[:2], ["breeze_cursors", theme.CURSOR])
            self.assertEqual(self.controller.restore()["result"], "restored")
            self.assertEqual(reloads[-2:], ["breeze_cursors", theme.CURSOR])
        self.assertEqual(self.entries("kcminputrc")[("[Mouse]", "cursorSize")], "36")
        self.assertFalse(any(call[0].startswith("plasma-apply") for call in self.process.calls))
        self.assertFalse(any(call[0] == "busctl" and call[3] in {"/kdeglobals", "/kcminputrc", "/kwinrc"} for call in self.process.calls))

    def test_restore_does_not_move_cursor_backup_through_changed_parent(self):
        cursor = self.local_cursor()
        self.controller.apply()
        backup = Path(self.controller.load()["cursor_overrides"][0]["backup"])
        icons = cursor.parent
        saved = self.home / "icons-before-parent-edit"
        icons.rename(saved)
        replacement = self.home / "managed-icons"
        replacement.mkdir()
        replacement_cursor = replacement / theme.CURSOR
        replacement_cursor.symlink_to(self.share / "icons" / theme.CURSOR, target_is_directory=True)
        icons.symlink_to(replacement, target_is_directory=True)
        result = self.controller.restore()
        self.assertEqual(result["result"], "restore-incomplete")
        self.assertTrue(replacement_cursor.is_symlink())
        self.assertTrue((backup / "original").is_file())
        self.assertTrue(self.controller.state_file.exists())

    def test_gtk_skip_restores_inherited_same_id_cursor(self):
        self.local_cursor()
        self.put("kcminputrc", "[Mouse]\ncursorSize=36\n")
        real_run = self.backend.run

        def effective(*args):
            if args[0] == "kreadconfig6" and args[args.index("--key") + 1] == "cursorTheme":
                return self.entries("kcminputrc").get(("[Mouse]", "cursorTheme"), theme.CURSOR)
            return real_run(*args)

        with mock.patch.object(self.backend, "run", side_effect=effective):
            self.controller.apply(skip=("gtk",))
            # KConfig can elide a value identical to the system default.
            self.put("kcminputrc", "[Mouse]\ncursorSize=36\n")
            with mock.patch.object(self.backend, "refresh_cursor", wraps=self.backend.refresh_cursor) as reload:
                self.assertEqual(self.controller.restore()["result"], "restored")
                self.assertEqual(reload.call_count, 2)
        self.assertEqual(self.entries("kcminputrc"), {("[Mouse]", "cursorSize"): "36"})

    def test_v2_cursor_alias_record_without_parent_identity_restores(self):
        cursor = self.local_cursor()
        (self.home / ".icons").symlink_to(cursor.parent, target_is_directory=True)
        self.controller.apply()
        state = self.controller.load()
        state["version"] = 2
        state.pop("components", None)
        state.pop("request_options", None)
        for item in state["cursor_overrides"]:
            item.pop("parent", None)
        self.controller.save(state)
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual((cursor / "original").read_bytes(), b"untouched original cursor directory")
        self.assertTrue((self.home / ".icons").is_symlink())

    def test_core_symlink_failure_creates_no_state_or_config(self):
        self.managed("kdeglobals")
        before = self.tree()
        with self.assertRaisesRegex(theme.ThemeError, "符号链接"):
            self.controller.apply()
        self.assertEqual(self.tree(), before)
        self.assertFalse(self.controller.state_dir.exists())
        self.assertEqual(self.process.calls, [])

    def test_explicit_skips_restore_only_applied_components(self):
        self.put("kcminputrc", "[Mouse]\ncursorTheme=original\ncursorSize=36\n")
        self.put("ghostty/config", "font-size = 13\n")
        originals = list(self.process.desktops)
        skipped = ("cursor", "wallpaper", "lockscreen", "gtk", "ghostty", "konsole")
        self.controller.apply(skip=skipped)
        self.assertEqual(self.controller.load()["version"], 3)
        self.assertEqual(self.entries("kcminputrc"), {("[Mouse]", "cursorTheme"): "original", ("[Mouse]", "cursorSize"): "36"})
        self.assertEqual(self.process.desktops, originals)
        self.assertFalse((self.controller.state_dir / "ghostty.conf").exists())
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual(self.process.desktops, originals)
        self.assertEqual((self.config / "ghostty/config").read_text(), "font-size = 13\n")
        self.assertFalse(any(call[0] == "plasma-apply-cursortheme" for call in self.process.calls))

    def test_same_options_repeat_but_changed_options_preserve_original_record(self):
        self.controller.apply(skip=("ghostty", "gtk"))
        original = self.controller.state_file.read_bytes()
        count = len(self.process.calls)
        self.assertEqual(self.controller.apply(skip=("gtk", "ghostty", "gtk"))["result"], "already-applied")
        self.assertEqual(len(self.process.calls), count)
        with self.assertRaisesRegex(theme.ThemeError, "restore"):
            self.controller.apply(skip=("ghostty",))
        self.assertEqual(self.controller.state_file.read_bytes(), original)

    def test_unknown_or_core_skip_has_zero_side_effects(self):
        for name in ("typo", "core"):
            with self.subTest(name=name):
                before = self.tree()
                with self.assertRaises((theme.ThemeError, ValueError)):
                    self.controller.apply(skip=(name,))
                self.assertEqual(self.tree(), before)
                self.assertEqual(self.process.calls, [])

    def test_dry_run_never_writes_or_calls_mutators(self):
        self.put("kdeglobals", "[General]\nColorScheme=Before\n")
        self.managed("ghostty/config")
        self.local_cursor()
        before = self.tree()
        result = self.controller.apply(dry_run=True, skip=("gtk",))
        self.assertEqual(self.tree(), before)
        self.assertFalse(self.controller.state_dir.exists())
        self.assertEqual(result["components"]["ghostty"]["status"], "skipped")
        self.assertEqual(result["components"]["gtk"]["status"], "skipped")
        allowed = {"qdbus", "kreadconfig6"}
        self.assertTrue(all(args[0] in allowed for args in self.process.calls))
        self.assertFalse(any("kaltsit:set-wallpapers" in args[-1] for args in self.process.calls))
        encoded = json.dumps(result)
        self.assertIn("ColorScheme", encoded)
        self.assertIn("Before", encoded)
        self.assertIn(theme.SCHEME, encoded)

    def test_missing_multiple_commands_report_together_before_changes(self):
        before = self.tree()
        missing = ["kwriteconfig6", "plasma-apply-colorscheme", "qdbus"]
        with mock.patch.object(self.backend, "missing_commands", return_value=missing):
            with self.assertRaises(theme.ThemeError) as error:
                self.controller.apply()
            for command in missing:
                self.assertIn(command, str(error.exception))
            self.assertIn("KDE Plasma", str(error.exception))
        self.assertEqual(self.tree(), before)
        self.assertEqual(self.process.calls, [])

    def test_missing_tools_do_not_break_status_or_dry_run(self):
        before = self.tree()
        with mock.patch.object(self.backend, "missing_commands", return_value=["kwriteconfig6", "qdbus"]):
            status = self.controller.status()
            self.assertEqual(status["phase"], "not-applied")
            result = self.controller.apply(dry_run=True)
            self.assertIn("qdbus", json.dumps(result))
        self.assertEqual(self.tree(), before)

    def test_offline_status_reads_inherited_config_with_user_precedence(self):
        first, second = self.home / "system-first", self.home / "system-second"
        first.mkdir()
        second.mkdir()
        (first / "kdeglobals").write_text("[General]\nColorScheme=SystemFirst\n[Icons]\nTheme=InheritedIcons\n")
        (second / "kdeglobals").write_text("[General]\nColorScheme=SystemSecond\n[Icons]\nTheme=WrongIcons\n")
        (first / "plasmarc").write_text("[Theme]\nname=InheritedStyle\n")
        env = dict(self.env, XDG_CONFIG_DIRS=f"{first}:relative/ignored:{second}")
        controller = theme.Controller(self.share, env, self.backend)
        before = self.tree()
        result = controller.status()
        self.assertEqual(result["current_color_scheme"], "SystemFirst")
        self.assertEqual(result["current_icons"], "InheritedIcons")
        self.assertEqual(result["current_plasma_style"], "InheritedStyle")
        self.assertEqual(self.tree(), before)
        self.assertEqual(self.process.calls, [])
        self.put("kdeglobals", "[General]\nColorScheme=LocalChoice\n")
        self.assertEqual(controller.status()["current_color_scheme"], "LocalChoice")
        self.assertEqual(controller.status()["current_icons"], "InheritedIcons")

    def test_custom_wallpaper_applies_both_surfaces_and_restores(self):
        from PIL import Image
        path = self.home / "custom image.png"
        Image.new("RGB", (30, 20), "#f4f7f2").save(path)
        desktops = list(self.process.desktops)
        self.put("kscreenlockerrc", "[Greeter][Wallpaper][org.kde.image][General]\nImage=file:///old-lock.png\nFillMode=0\n")
        old = self.entries("kscreenlockerrc")
        self.controller.apply(wallpaper=path)
        for desktop in self.process.desktops:
            self.assertEqual(desktop["image"], path.as_uri())
            self.assertEqual(desktop["fill_mode"], 2)
        lock = self.entries("kscreenlockerrc")
        self.assertEqual(lock[("[Greeter]", "WallpaperPlugin")], theme.LOCK_WALLPAPER)
        self.assertEqual(lock[(f"[Greeter][Wallpaper][{theme.LOCK_WALLPAPER}][General]", "Image")], path.as_uri())
        self.assertEqual(lock[("[Greeter][Wallpaper][org.kde.image][General]", "Image")], "file:///old-lock.png")
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual(self.process.desktops, desktops)
        self.assertEqual(self.entries("kscreenlockerrc"), old)

    def test_missing_lock_wallpaper_resources_fail_before_changes_and_allow_skip(self):
        (self.share / "plasma/wallpapers" / theme.LOCK_WALLPAPER / "contents/ui/main.qml").unlink()
        before = self.tree()
        with self.assertRaisesRegex(theme.ThemeError, "锁屏"):
            self.controller.apply()
        self.assertEqual(self.tree(), before)
        self.assertEqual(self.process.calls, [])
        self.assertFalse(self.controller.state_dir.exists())
        self.controller.apply(skip=("lockscreen",))
        self.assertEqual(self.controller.status()["components"]["lockscreen"]["status"], "skipped")
        self.assertEqual(self.controller.restore()["result"], "restored")

    def test_custom_wallpaper_option_idempotence_and_change_guard(self):
        from PIL import Image
        first = self.home / "first.png"
        second = self.home / "second.png"
        Image.new("RGB", (8, 8), "white").save(first)
        Image.new("RGB", (8, 8), "green").save(second)
        self.controller.apply(wallpaper=first)
        original = self.controller.state_file.read_bytes()
        count = len(self.process.calls)
        self.assertEqual(self.controller.apply(wallpaper=first)["result"], "already-applied")
        self.assertEqual(len(self.process.calls), count)
        with self.assertRaisesRegex(theme.ThemeError, "restore"):
            self.controller.apply(wallpaper=second)
        self.assertEqual(self.controller.state_file.read_bytes(), original)

    def test_missing_invalid_and_truncated_wallpapers_fail_before_writes(self):
        invalid = self.home / "not-an-image.jpg"
        invalid.write_bytes(b"not an image")
        truncated = self.home / "truncated.png"
        truncated.write_bytes(b"\x89PNG\r\n\x1a\n")
        for path in (self.home / "missing.png", invalid, truncated, self.home, Path("relative.png")):
            with self.subTest(path=path):
                before = self.tree()
                with self.assertRaises(theme.ThemeError):
                    self.controller.apply(wallpaper=path)
                self.assertEqual(self.tree(), before)
                self.assertEqual(self.process.calls, [])

    def test_v1_v2_restore_without_old_ghostty_theme_file(self):
        for version in (1, 2):
            with self.subTest(version=version):
                self.put("ghostty/config", "font-size = 14\n")
                self.controller.apply()
                record = self.controller.load()
                record["version"] = version
                record.pop("components", None)
                record.pop("request_options", None)
                if version == 1:
                    record.pop("cursor_overrides", None)
                self.controller.save(record)
                (self.controller.state_dir / "ghostty.conf").write_text("theme = /nix/store/nonexistent-garbage-collected/share/ghostty/theme\n")
                self.assertEqual(self.controller.restore()["result"], "restored")
                self.assertEqual((self.config / "ghostty/config").read_text(), "font-size = 14\n")
                self.assertFalse(self.controller.state_file.exists())

    def test_partial_failure_keeps_skipped_managed_component_untouched(self):
        path, target, old = self.managed("ghostty/config")
        self.put("plasmarc", "[Theme]\nname=before\n")
        self.process.fail = "plasma-apply-cursortheme"
        with self.assertRaisesRegex(theme.ThemeError, "已自动恢复"):
            self.controller.apply()
        self.assertEqual(self.entries("plasmarc"), {("[Theme]", "name"): "before"})
        self.assertTrue(path.is_symlink())
        self.assertEqual(target.read_bytes(), old)
        self.assertFalse(self.controller.state_file.exists())

    def test_gtk_export_triggered_by_final_notification_is_in_restore_record(self):
        self.put("gtk-3.0/colors.css", "/* original palette */\n")
        process = self.process

        def exporting_runner(args, **kwargs):
            result = process(args, **kwargs)
            if args[0] == "busctl" and args[3] == "/kdeglobals":
                scheme = self.entries("kdeglobals").get(("[General]", "ColorScheme"))
                content = "/* final complete palette */\n" if scheme == theme.SCHEME else "/* original palette */\n"
                theme.atomic_text(self.config / "gtk-3.0/colors.css", content)
            return result

        self.backend.runner = exporting_runner
        self.controller.apply()
        state = self.controller.load()
        self.assertEqual(state["after"]["gtk-3.0/colors.css"], "/* final complete palette */\n")
        self.assertEqual(self.controller.restore()["result"], "restored")

    def test_cli_unknown_skip_does_not_instantiate_controller(self):
        with mock.patch.object(theme, "Controller") as constructor, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                theme.main(["--data-dir", str(self.share), "apply", "--skip", "typo"])
            constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
