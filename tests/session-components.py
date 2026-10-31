#!/usr/bin/env python3
"""Check component boundaries against real KDE, in the private test session only."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

from PIL import Image

root = Path(os.environ["KALTSIT_TEST_ROOT"])
assert Path(os.environ["HOME"]) == root / "home"
assert Path(os.environ["XDG_RUNTIME_DIR"]) == root / "runtime"
spec = importlib.util.spec_from_file_location("theme_components", os.environ["KALTSIT_CONTROLLER"])
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)
controller = theme.Controller(Path(os.environ["KALTSIT_SHARE"]))
assert not controller.state_file.exists()


def files(path):
    return {str(p.relative_to(path)): ("link", os.readlink(p)) if p.is_symlink()
            else ("file", hashlib.sha256(p.read_bytes()).hexdigest())
            for p in path.rglob("*") if p.is_file() or p.is_symlink()}


# Explicitly exercise the live GTK synchronization module, not just an idle bus.
loaded = controller.backend.run("qdbus", "org.kde.kded6", "/kded", "org.kde.kded6.loadModule", "gtkconfig")
assert loaded == "true", loaded
time.sleep(2)
managed = root / "managed-components"
managed.mkdir()
names = {
    "cursor": ["kcminputrc"],
    "wallpaper": ["plasma-org.kde.plasma.desktop-appletsrc"],
    "lockscreen": ["kscreenlockerrc"],
    "gtk": ["gtk-3.0/settings.ini", "gtk-4.0/settings.ini", "gtk-3.0/colors.css", "gtk-4.0/colors.css", "gtk-3.0/gtk.css", "gtk-4.0/gtk.css"],
    "ghostty": ["ghostty/config"],
    "konsole": ["konsolerc"],
}
restoration = []
for component, entries in names.items():
    for name in entries:
        path = controller.config / name
        original = path.read_bytes() if path.exists() else None
        assert not path.is_symlink(), path
        target = managed / name.replace("/", "_")
        target.write_bytes(original if original is not None else b"# managed component fixture\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        path.symlink_to(target)
        restoration.append((path, target, original))
time.sleep(2)
targets_before = files(managed)
links_before = {str(path): os.readlink(path) for path, _, _ in restoration}
wallpapers_before = controller.backend.wallpapers()
dry_before = files(controller.config)
state_before = files(controller.state_dir)
preview = controller.apply(dry_run=True)
assert files(controller.config) == dry_before
assert files(controller.state_dir) == state_before
for component in names:
    assert preview["components"][component]["status"] == "skipped", preview
applied = controller.apply()
assert applied["result"] == "partially-applied", applied
time.sleep(3)
assert files(managed) == targets_before, (targets_before, files(managed))
assert all(path.is_symlink() and os.readlink(path) == links_before[str(path)] for path, _, _ in restoration)
assert controller.backend.wallpapers() == wallpapers_before
record = controller.state_file.read_bytes()
assert controller.apply()["result"] == "already-applied"
assert controller.state_file.read_bytes() == record
assert controller.restore()["result"] == "restored"
time.sleep(3)
assert files(managed) == targets_before
assert controller.backend.wallpapers() == wallpapers_before
for path, target, original in restoration:
    assert path.is_symlink() and os.readlink(path) == str(target)
    path.unlink()
    if original is not None:
        path.write_bytes(original)

# Exercise GTK skipped with cursor enabled, including a same-ID resource reload.
controller.backend.write_key(controller.config / "kcminputrc", "[Mouse]", "cursorTheme", theme.CURSOR)
time.sleep(2)
gtk_restoration = []
for name in names["gtk"]:
    path = controller.config / name
    original = path.read_bytes() if path.exists() else None
    target = managed / ("gtk-only-" + name.replace("/", "_"))
    target.write_bytes(original if original is not None else b"# managed GTK fixture\n")
    path.unlink(missing_ok=True)
    path.symlink_to(target)
    gtk_restoration.append((path, target, original))
gtk_before = files(managed)
cursor_reloads = []


class CursorProbe(theme.Backend):
    def refresh_cursor(self):
        current = self.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme")
        cursor_reloads.append(current)
        super().refresh_cursor()


cursor_probe = theme.Controller(Path(os.environ["KALTSIT_SHARE"]), backend=CursorProbe(dict(os.environ)))
assert controller.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme") == theme.CURSOR
assert cursor_probe.apply()["result"] == "partially-applied"
time.sleep(3)
assert files(managed) == gtk_before
assert cursor_reloads[:2] == ["breeze_cursors", theme.CURSOR], cursor_reloads
assert cursor_probe.restore()["result"] == "restored"
time.sleep(3)
assert files(managed) == gtk_before
assert cursor_reloads[-2:] == ["breeze_cursors", theme.CURSOR], cursor_reloads
for path, target, original in gtk_restoration:
    assert path.is_symlink() and os.readlink(path) == str(target)
    path.unlink()
    if original is not None:
        path.write_bytes(original)

# A supplied image is checked by a decoder and written to both wallpaper targets.
custom = root / "custom wallpaper.png"
Image.new("RGB", (300, 200), "#F4F7F2").save(custom)
old_wallpapers = controller.backend.wallpapers()
for version in (3, 4):
    path = controller.config / f"gtk-{version}.0/settings.ini"
    theme.atomic_text(path, theme.edit_ini(theme.read_text(path), {
        ("[Settings]", "gtk-font-name"): "Theme preservation fixture 11",
        ("[Settings]", "gtk-cursor-theme-name"): "Adwaita",
    }))
applied = controller.apply(wallpaper=custom)
assert applied["result"] == "applied", applied
for version in (3, 4):
    assert theme.ini_entries(theme.read_text(controller.config / f"gtk-{version}.0/settings.ini"))[("[Settings]", "gtk-font-name")] == "Theme preservation fixture 11"
assert all(item["image"] == custom.as_uri() and item["fill_mode"] == 2 for item in controller.backend.wallpapers())
lock = theme.ini_entries(theme.read_text(controller.config / "kscreenlockerrc"))
assert lock[(f"[Greeter][Wallpaper][{theme.LOCK_WALLPAPER}][General]", "Image")] == custom.as_uri()
assert lock[(f"[Greeter][Wallpaper][{theme.LOCK_WALLPAPER}][General]", "FillMode")] == "2"
assert controller.restore()["result"] == "restored"
time.sleep(3)
for version in (3, 4):
    assert theme.ini_entries(theme.read_text(controller.config / f"gtk-{version}.0/settings.ini"))[("[Settings]", "gtk-cursor-theme-name")] == "Adwaita"
assert controller.backend.wallpapers() == old_wallpapers

results = {
    "gtkconfig_module_loaded": True,
    "managed_components": list(names),
    "managed_links_and_targets_unchanged_after_apply_repeat_restore": True,
    "dry_run_configuration_and_state_unchanged": True,
    "custom_wallpaper_desktop_and_lockscreen_fill_mode_2": True,
    "custom_wallpaper_restored": True,
    "gtk_only_skip_preserves_targets_with_live_cursor_apply_restore": True,
    "same_id_cursor_reload_events": cursor_reloads,
    "existing_custom_gtk_fonts_preserved": True,
    "independent_gtk_cursor_restored_after_daemon_settles": True,
}
(root / "component-probes.json").write_text(json.dumps(results, indent=2) + "\n")
