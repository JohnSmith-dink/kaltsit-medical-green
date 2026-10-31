"""No session bus, installed apps, or real HOME is touched by these tests."""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import types
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location(
    "kaltsit_theme", Path(__file__).resolve().parents[1] / "tools/kaltsit_theme.py"
)
theme = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(theme)


class FakeProcess:
    """subprocess.run replacement emulates only the documented mutation boundary."""
    def __init__(self, config):
        self.config = config
        self.calls = []
        self.environments = []
        self.palette_inputs = []
        self.cursor_inputs = []
        self.desktops = [
            {"id": 2, "plugin": "org.kde.image", "image_exists": True, "image": "file:///before.jpg",
             "fill_mode_exists": True, "fill_mode": 0},
            {"id": 8, "plugin": "org.kde.slideshow", "image_exists": False, "image": "",
             "fill_mode_exists": False, "fill_mode": 2},
        ]
        self.fail = None

    def set_key(self, name, group, key, value):
        path = self.config / name
        theme.atomic_text(path, theme.edit_ini(theme.read_text(path), {(group, key): value}))

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        self.environments.append(dict(kwargs["env"]))
        output = ""
        if args[0] == "plasma-apply-lookandfeel":
            self.set_key("kdeglobals", "[KDE]", "LookAndFeelPackage", theme.THEME)
            self.set_key("kdeglobals", "[General]", "font", "Unwanted Font,12")
            self.set_key("kwinrc", "[Xwayland]", "Scale", "1")
            self.set_key("kcminputrc", "[Mouse]", "cursorSize", "24")
            self.set_key("kdedefaults/kdeglobals", "[General]", "ColorScheme", theme.SCHEME)
            self.set_key("kdedefaults/kdeglobals", "[General]", "fixed", "Unwanted Mono,12")
            theme.atomic_text(self.config / "kdedefaults/package", theme.THEME)
        elif args[0] == "plasma-apply-colorscheme":
            self.palette_inputs.append(theme.ini_entries(theme.read_text(self.config / "kdeglobals")))
            self.set_key("kdeglobals", "[General]", "ColorScheme", theme.SCHEME)
            self.set_key("kdeglobals", "[Colors:Window]", "BackgroundNormal", "247,250,246")
        elif args[0] == "plasma-apply-cursortheme":
            self.cursor_inputs.append(theme.ini_entries(theme.read_text(self.config / "kcminputrc")))
            self.set_key("kcminputrc", "[Mouse]", "cursorTheme", args[-1])
            self.set_key("kcminputrc", "[Mouse]", "cursorSize", args[args.index("--size") + 1])
        elif args[0] == "kreadconfig6":
            key = args[args.index("--key") + 1]
            output = theme.ini_entries(theme.read_text(self.config / "kcminputrc")).get(
                ("[Mouse]", key), args[args.index("--default") + 1])
        elif args[0] == "kwriteconfig6":
            path = Path(args[args.index("--file") + 1])
            if not path.is_absolute():
                path = Path(kwargs["env"]["XDG_CONFIG_HOME"]) / path
            groups = [args[i + 1] for i, arg in enumerate(args) if arg == "--group"]
            group = "".join(f"[{part}]" for part in groups)
            key = args[args.index("--key") + 1]
            value = None if "--delete" in args else args[-1]
            theme.atomic_text(path, theme.edit_ini(theme.read_text(path), {(group, key): value}))
        elif args[0] == "qdbus" and "evaluateScript" in args[-2]:
            code = args[-1]
            if "kaltsit:snapshot" in code:
                output = json.dumps(self.desktops)
            elif "kaltsit:set-wallpapers" in code:
                items = json.loads(re.search(r"var saved = (.*);", code).group(1))
                existing = {item["id"]: item for item in self.desktops}
                existing.update({item["id"]: item for item in items})
                self.desktops = list(existing.values())
        if self.fail == args[0]:
            self.fail = None  # fail once, so rollback itself can be exercised
            raise subprocess.CalledProcessError(1, args, stderr="simulated failure")
        return types.SimpleNamespace(stdout=output, stderr="", returncode=0)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / ".config"
        self.share = self.home / "package/share"
        wallpaper = self.share / f"wallpapers/{theme.SCHEME}/contents/images/3840x2160.jpg"
        wallpaper.parent.mkdir(parents=True)
        wallpaper.write_bytes(b"fake image; no image decoder needed for the controller")
        self.env = {"HOME": str(self.home), "PATH": "/not-used"}
        self.process = FakeProcess(self.config)
        self.backend = theme.Backend(self.env, runner=self.process)
        self.controller = theme.Controller(self.share, self.env, self.backend)

    def put(self, name, value):
        theme.atomic_text(self.config / name, value)

    def entries(self, name):
        return theme.ini_entries(theme.read_text(self.config / name))

    def test_status_is_read_only_and_offline(self):
        result = self.controller.status()
        self.assertEqual(result["phase"], "not-applied")
        self.assertFalse(self.controller.state_dir.exists())
        self.assertEqual(self.process.calls, [])

    def test_apply_restore_preserves_unrelated_edits_and_layout(self):
        self.put("kdeglobals", "# user comment\n[General]\nColorScheme=BreezeLight\nBrowserApplication=browser.desktop\n")
        self.put("plasma-org.kde.plasma.desktop-appletsrc", "[Containments][2]\nlocation=4\n[Containments][5]\nplugin=org.kde.panel\n")
        layout = (self.config / "plasma-org.kde.plasma.desktop-appletsrc").read_text()
        original_wallpapers = list(self.process.desktops)
        self.controller.apply()
        self.assertTrue(all(item["fill_mode"] == 2 for item in self.process.desktops))
        self.assertEqual(self.entries("kscreenlockerrc")[("[Greeter][Wallpaper][org.kde.image][General]", "FillMode")], "2")
        self.process.set_key("kdeglobals", "[General]", "BrowserApplication", "new-browser.desktop")
        self.process.set_key("kdeglobals", "[UserSettings]", "NewValue", "retained")
        result = self.controller.restore()
        self.assertEqual(result["result"], "restored")
        keys = self.entries("kdeglobals")
        self.assertEqual(keys[("[General]", "ColorScheme")], "BreezeLight")
        self.assertEqual(keys[("[General]", "BrowserApplication")], "new-browser.desktop")
        self.assertEqual(keys[("[UserSettings]", "NewValue")], "retained")
        self.assertNotIn(("[Icons]", "Theme"), keys)
        self.assertEqual(self.process.desktops, original_wallpapers)
        self.assertEqual((self.config / "plasma-org.kde.plasma.desktop-appletsrc").read_text(), layout)
        self.assertFalse(any("--resetLayout" in args for args in self.process.calls))

    def test_restore_removes_new_keys_files_and_defaults(self):
        self.controller.apply()
        self.assertTrue((self.config / "kdedefaults/package").exists())
        self.assertTrue((self.config / "kscreenlockerrc").exists())
        self.controller.restore()
        self.assertFalse((self.config / "kdedefaults/package").exists())
        self.assertFalse((self.config / "kdedefaults/kdeglobals").exists())
        self.assertFalse((self.config / "kscreenlockerrc").exists())
        self.assertFalse(self.controller.state_file.exists())
        self.assertEqual(self.controller.restore()["result"], "nothing-to-restore")

    def test_idempotent_apply_preserves_first_restore_point(self):
        self.put("kdeglobals", "[General]\nColorScheme=Original\n")
        self.controller.apply()
        state = self.controller.state_file.read_bytes()
        count = len(self.process.calls)
        self.assertEqual(self.controller.apply()["result"], "already-applied")
        self.assertEqual(self.controller.state_file.read_bytes(), state)
        self.assertEqual(len(self.process.calls), count)

    def test_plasma_style_restore_keeps_unrelated_settings(self):
        self.put("plasmarc", "[Theme]\nname=custom-old\n[Other]\nKeep=before\n")
        self.controller.apply()
        self.assertEqual(self.entries("plasmarc")[("[Theme]", "name")], theme.SCHEME)
        self.assertEqual(self.controller.status()["current_plasma_style"], theme.SCHEME)
        self.process.set_key("plasmarc", "[Other]", "Keep", "later")
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual(self.entries("plasmarc"), {("[Theme]", "name"): "custom-old", ("[Other]", "Keep"): "later"})

    def test_style_conflict_is_not_overwritten_on_restore(self):
        self.put("plasmarc", "[Theme]\nname=custom-old\n")
        self.controller.apply()
        self.process.set_key("plasmarc", "[Theme]", "name", "user-later")
        self.assertEqual(self.controller.restore()["result"], "restore-incomplete")
        self.assertEqual(self.entries("plasmarc")[("[Theme]", "name")], "user-later")

    def test_failure_after_new_style_write_restores_style(self):
        self.put("plasmarc", "[Theme]\nname=custom-old\n")
        self.process.fail = "plasma-apply-cursortheme"
        with self.assertRaisesRegex(theme.ThemeError, "已自动恢复"):
            self.controller.apply()
        self.assertEqual(self.entries("plasmarc"), {("[Theme]", "name"): "custom-old"})
        self.assertFalse(self.controller.state_file.exists())

    def test_legacy_record_restores_before_upgrade_without_losing_backup(self):
        self.put("kdeglobals", "[General]\nColorScheme=BeforeV1\n")
        self.put("plasmarc", "[Theme]\nname=custom-old\n")
        self.controller.apply()
        legacy = self.controller.load()
        del legacy["theme_version"]
        legacy["version"] = 1
        # v1.0 used Breeze; its state schema has no application version.
        self.process.set_key("plasmarc", "[Theme]", "name", "default")
        legacy["after"]["plasmarc"] = theme.read_text(self.config / "plasmarc")
        self.controller.save(legacy)
        backup = self.controller.state_file.read_bytes()
        count = len(self.process.calls)
        self.assertEqual(self.controller.status()["applied_version"], "1.0.0")
        self.assertTrue(self.controller.status()["upgrade_available"])
        with self.assertRaisesRegex(theme.ThemeError, "先执行 kaltsit-theme restore"):
            self.controller.apply()
        self.assertEqual(self.controller.state_file.read_bytes(), backup)
        self.assertEqual(len(self.process.calls), count)
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual(self.entries("kdeglobals")[("[General]", "ColorScheme")], "BeforeV1")
        self.assertEqual(self.entries("plasmarc")[("[Theme]", "name")], "custom-old")
        self.assertEqual(self.controller.apply()["result"], "applied")
        self.assertEqual(self.controller.status()["applied_version"], theme.VERSION)
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertEqual(self.entries("kdeglobals")[("[General]", "ColorScheme")], "BeforeV1")

    def local_cursor(self):
        target = self.share / "icons" / theme.CURSOR / "cursors"
        target.mkdir(parents=True, exist_ok=True)
        (target / "left_ptr").write_bytes(b"new multi-size cursor fixture")
        path = self.home / ".local/share/icons" / theme.CURSOR
        path.mkdir(parents=True)
        (path / "original").write_bytes(b"untouched original cursor directory")
        return path

    def test_local_cursor_shadow_roundtrips_original_directory(self):
        path = self.local_cursor()
        self.controller.apply()
        self.assertTrue(path.is_symlink())
        self.assertEqual(path.resolve(), self.share / "icons" / theme.CURSOR)
        state = self.controller.load()
        self.assertEqual(state["version"], 2, "Old controllers must reject records containing resource backups")
        backup = Path(state["cursor_overrides"][0]["backup"])
        self.assertEqual((backup / "original").read_bytes(), b"untouched original cursor directory")
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertFalse(path.is_symlink())
        self.assertEqual((path / "original").read_bytes(), b"untouched original cursor directory")
        self.assertFalse(backup.exists())

    def test_local_cursor_conflict_keeps_backup_and_user_directory(self):
        path = self.local_cursor()
        self.controller.apply()
        backup = Path(self.controller.load()["cursor_overrides"][0]["backup"])
        path.unlink()
        path.mkdir()
        (path / "later").write_text("user edit")
        self.assertEqual(self.controller.restore()["result"], "restore-incomplete")
        self.assertEqual((path / "later").read_text(), "user edit")
        self.assertTrue((backup / "original").exists())
        (path / "later").unlink()
        path.rmdir()
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertTrue((path / "original").exists())

    def test_user_link_already_pointing_to_current_assets_is_untouched(self):
        target = self.share / "icons" / theme.CURSOR
        target.mkdir(parents=True)
        path = self.home / ".local/share/icons" / theme.CURSOR
        path.parent.mkdir(parents=True)
        path.symlink_to(target)
        self.controller.apply()
        self.assertEqual(self.controller.load()["cursor_overrides"], [])
        self.controller.restore()
        self.assertTrue(path.is_symlink())
        self.assertEqual(path.resolve(), target)

    def test_failure_between_cursor_backup_and_link_creation_rolls_back(self):
        path = self.local_cursor()
        with mock.patch.object(Path, "symlink_to", side_effect=OSError("injected link failure")):
            with self.assertRaisesRegex(theme.ThemeError, "已自动恢复"):
                self.controller.apply()
        self.assertFalse(path.is_symlink())
        self.assertTrue((path / "original").exists())
        self.assertFalse(self.controller.state_file.exists())

    def test_aliased_icon_directories_are_only_moved_once(self):
        path = self.local_cursor()
        (self.home / ".icons").symlink_to(path.parent)
        self.controller.apply()
        self.assertEqual(len(self.controller.load()["cursor_overrides"]), 1)
        self.assertEqual(self.controller.restore()["result"], "restored")
        self.assertTrue((path / "original").exists())
        self.assertTrue((self.home / ".icons").is_symlink())

    def test_same_cursor_id_reloads_frames_and_keeps_size(self):
        path = self.local_cursor()
        self.put("kcminputrc", f"[Mouse]\ncursorTheme={theme.CURSOR}\ncursorSize=36\n")
        self.controller.apply()
        cursor_calls = [args for args in self.process.calls if args[0] == "plasma-apply-cursortheme"]
        self.assertEqual([args[-1] for args in cursor_calls], ["breeze_cursors", theme.CURSOR])
        self.assertTrue(all(args[2] == "36" for args in cursor_calls))
        self.controller.restore()
        self.assertTrue((path / "original").exists())
        self.assertEqual(self.entries("kcminputrc")[("[Mouse]", "cursorSize")], "36")
        cursor_calls = [args for args in self.process.calls if args[0] == "plasma-apply-cursortheme"]
        self.assertEqual([args[-1] for args in cursor_calls[-2:]], ["breeze_cursors", theme.CURSOR])

    def test_kded_async_gtk_modules_and_fonts_do_not_block_restore(self):
        self.controller.apply()
        state = self.controller.load()
        for version in (3, 4):
            name = f"gtk-{version}.0/settings.ini"
            # kded first adds one module during apply, then adds another plus
            # desktop font/DPI values after the transaction snapshot.
            state["after"][name] = theme.edit_ini(state["after"][name], {
                ("[Settings]", "gtk-modules"): "colorreload-gtk-module",
            })
            self.process.set_key(name, "[Settings]", "gtk-modules",
                                 "colorreload-gtk-module:window-decorations-gtk-module")
            self.process.set_key(name, "[Settings]", "gtk-font-name", "Noto Sans, 10")
            self.process.set_key(name, "[Settings]", "gtk-xft-dpi", "147456")
        self.controller.save(state)
        result = self.controller.restore()
        self.assertEqual(result["result"], "restored")
        self.assertEqual(result["warnings"], [])
        for version in (3, 4):
            keys = self.entries(f"gtk-{version}.0/settings.ini")
            self.assertEqual(keys[("[Settings]", "gtk-modules")],
                             "colorreload-gtk-module:window-decorations-gtk-module")
            self.assertEqual(keys[("[Settings]", "gtk-font-name")], "Noto Sans, 10")
            self.assertEqual(keys[("[Settings]", "gtk-xft-dpi")], "147456")
            self.assertFalse(set(keys) & theme.GTK_OWNED_KEYS)

    def test_new_gtk_file_with_unowned_keys_is_not_unlinked(self):
        name = "gtk-3.0/settings.ini"
        applied = "[Settings]\ngtk-theme-name=Breeze\ngtk-modules=colorreload-gtk-module\n"
        self.put(name, applied)
        warnings = self.controller.restore_files({"before": {name: None}, "after": {name: applied}})
        self.assertEqual(warnings, [])
        self.assertTrue((self.config / name).exists())
        self.assertEqual(self.entries(name), {("[Settings]", "gtk-modules"): "colorreload-gtk-module"})

    def test_preserve_font_scaling_and_cursor_size(self):
        self.put("kdeglobals", "[General]\nfont=Noto Sans,10\n")
        self.put("kwinrc", "[Xwayland]\nScale=1.5\n")
        self.put("kcminputrc", "[Mouse]\ncursorSize=48\n")
        self.controller.apply()
        self.assertEqual(self.entries("kdeglobals")[("[General]", "font")], "Noto Sans,10")
        self.assertEqual(self.entries("kwinrc")[("[Xwayland]", "Scale")], "1.5")
        self.assertEqual(self.entries("kcminputrc")[("[Mouse]", "cursorSize")], "48")
        self.assertIn(["plasma-apply-cursortheme", "--size", "48", theme.CURSOR], self.process.calls)
        self.assertNotIn(("[General]", "fixed"), self.entries("kdedefaults/kdeglobals"))

    def test_accent_neutralized_before_palette_and_restored(self):
        self.put("kdeglobals", "[General]\nAccentColor=255,0,0\naccentColorFromWallpaper=true\nColorScheme=Original\n")
        self.put("kdedefaults/kdeglobals", "[General]\nAccentColor=0,0,255\n")
        old = self.entries("kdeglobals")
        defaults = self.entries("kdedefaults/kdeglobals")
        self.controller.apply()
        palette_input = self.process.palette_inputs[0]
        self.assertEqual(palette_input[("[General]", "AccentColor")], "0,0,0,0")
        self.assertEqual(palette_input[("[General]", "accentColorFromWallpaper")], "false")
        self.assertNotIn(("[General]", "AccentColorFromWallpaper"), self.entries("kdeglobals"))
        self.controller.restore()
        self.assertEqual(self.entries("kdeglobals"), old)
        self.assertEqual(self.entries("kdedefaults/kdeglobals"), defaults)

    def test_kwriteconfig_uses_relative_name_and_explicit_xdg_root(self):
        self.controller.apply()
        writes = [(call, env) for call, env in zip(self.process.calls, self.process.environments)
                  if call[0] == "kwriteconfig6"]
        self.assertTrue(writes)
        for call, env in writes:
            self.assertFalse(Path(call[call.index("--file") + 1]).is_absolute())
            self.assertEqual(env["XDG_CONFIG_HOME"], str(self.config))
            self.assertIn("--notify", call)

    def test_exact_kconfig_notification_signature_paths_and_removed_keys(self):
        before = {"gtk-3.0/settings.ini": "[Top][Nested]\nRemoved=old\nSame=keep\n"}
        after = {"gtk-3.0/settings.ini": "[Top][Nested]\nSame=keep\nNew=value\n"}
        self.backend.notify_configs(before, after)
        expected = ["busctl", "--user", "emit", "/gtk_3_0/settings_ini", "org.kde.kconfig.notify",
                    "ConfigChanged", "a{saay}", "1", "Top\x1dNested", "2",
                    "3", "78", "101", "119", "7", "82", "101", "109", "111", "118", "101", "100"]
        self.assertEqual(self.process.calls, [expected])
        self.backend.notify_configs(after, after)
        self.backend.notify_configs({"gtk-3.0/colors.css": "old"}, {"gtk-3.0/colors.css": "new"})
        self.assertEqual(self.process.calls, [expected])

    def test_restore_uses_live_cursor_tool_before_precise_disk_restore(self):
        self.put("kcminputrc", "[Mouse]\ncursorSize=36\n")
        original = self.entries("kcminputrc")
        self.controller.apply()
        start = len(self.process.calls)
        self.controller.restore()
        restore_calls = self.process.calls[start:]
        self.assertIn(["plasma-apply-cursortheme", "--size", "36", "breeze_cursors"], restore_calls)
        self.assertEqual(self.process.cursor_inputs[-1][("[Mouse]", "cursorTheme")], theme.CURSOR)
        self.assertEqual(self.entries("kcminputrc"), original)
        emitted_paths = {args[3] for args in restore_calls if args[0] == "busctl"}
        self.assertIn("/kcminputrc", emitted_paths)
        self.assertIn("/kdeglobals", emitted_paths)

    def test_terminal_blocks_restore_only_their_own_content(self):
        self.put("ghostty/config", "font-size = 14\ncommand = zsh\n")
        self.put("konsolerc", "[Desktop Entry]\nDefaultProfile=Custom.profile\n")
        self.controller.apply()
        profile = self.home / f".local/share/konsole/{theme.SCHEME}.profile"
        self.assertIn("Parent=Custom.profile", profile.read_text())
        self.assertNotIn("Font=", profile.read_text())
        ghostty = self.config / "ghostty/config"
        with ghostty.open("a") as stream:
            stream.write("mouse-hide-while-typing = true\n")
        self.controller.restore()
        self.assertEqual(ghostty.read_text(), "font-size = 14\ncommand = zsh\nmouse-hide-while-typing = true\n")
        self.assertFalse(profile.exists())
        self.assertEqual(self.entries("konsolerc")[("[Desktop Entry]", "DefaultProfile")], "Custom.profile")

    def test_terminal_without_trailing_newline_roundtrips(self):
        self.put("ghostty/config", "font-size = 13")
        self.controller.apply()
        self.controller.restore()
        self.assertEqual((self.config / "ghostty/config").read_text(), "font-size = 13")

    def test_terminal_later_append_retains_line_boundary(self):
        self.put("ghostty/config", "font-size = 13")
        self.controller.apply()
        with (self.config / "ghostty/config").open("a") as stream:
            stream.write("command = zsh\n")
        self.controller.restore()
        self.assertEqual((self.config / "ghostty/config").read_text(), "font-size = 13\ncommand = zsh\n")

    def test_failed_command_rolls_back_partial_mutations(self):
        self.put("kdeglobals", "[General]\nColorScheme=Original\nfont=Original Font,11\n")
        before = self.entries("kdeglobals")
        original_wallpapers = list(self.process.desktops)
        self.process.fail = "plasma-apply-colorscheme"
        with self.assertRaisesRegex(theme.ThemeError, "已自动恢复"):
            self.controller.apply()
        self.assertEqual(self.entries("kdeglobals"), before)
        self.assertEqual(self.process.desktops, original_wallpapers)
        self.assertFalse(self.controller.state_file.exists())

    def test_missing_session_fails_before_theme_mutation(self):
        self.process.fail = "qdbus"
        with self.assertRaises(theme.ThemeError):
            self.controller.apply()
        self.assertFalse(self.controller.state_file.exists())
        self.assertFalse(any(args[0].startswith("plasma-apply") for args in self.process.calls))

    def test_conflicting_theme_edit_kept_with_recoverable_state(self):
        self.put("kdeglobals", "[General]\nColorScheme=Original\n")
        self.controller.apply()
        self.process.set_key("kdeglobals", "[General]", "ColorScheme", "UserLaterChoice")
        result = self.controller.restore()
        self.assertEqual(result["result"], "restore-incomplete")
        self.assertEqual(self.entries("kdeglobals")[("[General]", "ColorScheme")], "UserLaterChoice")
        self.assertTrue(self.controller.state_file.exists())
        self.process.set_key("kdeglobals", "[General]", "ColorScheme", "Original")
        self.assertEqual(self.controller.restore()["result"], "restored")

    def test_symlink_managed_configuration_refused_without_breaking_link(self):
        target = self.home / "managed-ghostty"
        target.write_text("font-size = 16\n")
        path = self.config / "ghostty/config"
        path.parent.mkdir(parents=True)
        path.symlink_to(target)
        with self.assertRaisesRegex(theme.ThemeError, "符号链接"):
            self.controller.apply()
        self.assertTrue(path.is_symlink())
        self.assertEqual(target.read_text(), "font-size = 16\n")
        self.assertEqual(self.process.calls, [])

    def test_xdg_overrides_honored(self):
        env = dict(self.env, XDG_CONFIG_HOME=str(self.home / "custom-config"),
                   XDG_DATA_HOME=str(self.home / "custom-data"), XDG_STATE_HOME=str(self.home / "custom-state"))
        controller = theme.Controller(self.share, env, self.backend)
        self.assertEqual(controller.config, self.home / "custom-config")
        self.assertEqual(controller.data, self.home / "custom-data")
        self.assertEqual(controller.state_dir, self.home / "custom-state/kaltsit-theme")

    def test_empty_xdg_paths_fall_back_to_home(self):
        env = dict(self.env, XDG_CONFIG_HOME="", XDG_DATA_HOME="", XDG_STATE_HOME="", XDG_DATA_DIRS="")
        controller = theme.Controller(self.share, env, self.backend)
        self.assertEqual(controller.config, self.home / ".config")
        self.assertEqual(controller.data, self.home / ".local/share")
        self.assertEqual(controller.state_dir, self.home / ".local/state/kaltsit-theme")
        self.assertEqual(controller.env["XDG_CONFIG_HOME"], str(self.home / ".config"))
        self.assertTrue(controller.env["XDG_DATA_DIRS"].endswith("/usr/local/share:/usr/share"))
        self.assertFalse(controller.state_dir.exists())

    def test_relative_xdg_paths_are_ignored(self):
        env = dict(self.env, XDG_CONFIG_HOME="config", XDG_DATA_HOME="data", XDG_STATE_HOME="state")
        controller = theme.Controller(self.share, env, self.backend)
        self.assertEqual(controller.config, self.home / ".config")
        self.assertEqual(controller.data, self.home / ".local/share")
        self.assertEqual(controller.state_dir, self.home / ".local/state/kaltsit-theme")

    def test_ini_patch_preserves_nested_groups_comments_and_unrelated_values(self):
        source = "# retain\n[Top][Nested]\nValue=escaped\\ntext\nOther=unchanged\n\n[Other]\nKey=retained\n"
        updated = theme.edit_ini(source, {("[Top][Nested]", "Value"): None,
                                          ("[Top][Nested]", "Added"): "new"})
        self.assertIn("# retain", updated)
        self.assertNotIn("Value=", updated)
        self.assertEqual(theme.ini_entries(updated)[("[Other]", "Key")], "retained")
        self.assertEqual(theme.ini_entries(updated)[("[Top][Nested]", "Added")], "new")


if __name__ == "__main__":
    unittest.main()
