#!/usr/bin/env python3
"""Exercise real KDE rollback and optional v1.0 migration in a private session."""
import importlib.util
import json
import os
from pathlib import Path

root = Path(os.environ["KALTSIT_TEST_ROOT"])
assert Path(os.environ["HOME"]) == root / "home"
assert Path(os.environ["XDG_RUNTIME_DIR"]) == root / "runtime"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


theme = module("current", os.environ["KALTSIT_CONTROLLER"])
share = Path(os.environ["KALTSIT_SHARE"])
controller = theme.Controller(share)


def owned():
    result = {}
    for name, identities in {
        "plasmarc": [("[Theme]", "name")],
        "kdeglobals": [("[General]", "ColorScheme"), ("[General]", "AccentColor"),
                       ("[KDE]", "LookAndFeelPackage"), ("[Icons]", "Theme")],
        "kcminputrc": [("[Mouse]", "cursorSize"), ("[Mouse]", "cursorTheme")],
    }.items():
        entries = theme.ini_entries(theme.read_text(controller.config / name))
        result[name] = [entries.get(key) for key in identities]
    return result


class FailAfterWallpaper(theme.Backend):
    pending = True

    def set_wallpapers(self, items):
        super().set_wallpapers(items)
        if self.pending:
            self.pending = False
            raise theme.ThemeError("deliberate failure after real wallpaper mutation")


local_cursor = controller.data / "icons" / theme.CURSOR
local_cursor.parent.mkdir(parents=True, exist_ok=True)
assert not local_cursor.exists() and not local_cursor.is_symlink()
original_target = str(Path(os.environ.get("KALTSIT_LEGACY_SHARE", str(share))) / "icons" / theme.CURSOR)
local_cursor.symlink_to(original_target, target_is_directory=True)
controller.backend.run("plasma-apply-cursortheme", "--size", "36", theme.CURSOR)
original = owned()
wallpapers = controller.backend.wallpapers()
faulty = theme.Controller(share, backend=FailAfterWallpaper(dict(os.environ)))
try:
    faulty.apply()
except theme.ThemeError as error:
    assert "已自动恢复" in str(error), str(error)
else:
    raise AssertionError("fault injection did not run")
assert owned() == original, (original, owned())
assert controller.backend.wallpapers() == wallpapers
assert not controller.state_file.exists()
assert local_cursor.is_symlink() and os.readlink(local_cursor) == original_target
results = {"real_failure_after_wallpaper": "rolled-back", "owned_keys_restored": True,
           "wallpapers_restored": True, "local_cursor_shadow_restored": True}

legacy_path = os.environ.get("KALTSIT_LEGACY_CONTROLLER")
if legacy_path:
    legacy = module("legacy", legacy_path)
    old = legacy.Controller(Path(os.environ["KALTSIT_LEGACY_SHARE"]))
    assert old.apply()["result"] == "applied"
    record = controller.state_file.read_bytes()
    assert controller.status()["applied_version"] == "1.0.0"
    try:
        controller.apply()
    except theme.ThemeError as error:
        assert "restore" in str(error)
    else:
        raise AssertionError("legacy backup was not protected")
    assert controller.state_file.read_bytes() == record
    restored = controller.restore()
    assert restored["result"] == "restored", restored
    assert owned() == original
    assert controller.apply()["result"] == "applied"
    assert local_cursor.resolve() == share / "icons" / theme.CURSOR
    try:
        old.status()
    except legacy.ThemeError:
        results["legacy_reader_rejects_resource_backup_schema"] = True
    else:
        raise AssertionError("old controller accepted a resource backup it cannot restore")
    assert controller.apply()["result"] == "already-applied"
    restored = controller.restore()
    assert restored["result"] == "restored", restored
    assert owned() == original
    assert os.readlink(local_cursor) == original_target
    results["v1_0_to_v1_1"] = "legacy apply; backup protected; restore; apply; repeat; restore"
    results["legacy_backup_unchanged"] = True

previous_path = os.environ.get("KALTSIT_PREVIOUS_CONTROLLER")
if previous_path:
    previous = module("previous", previous_path)
    old = previous.Controller(Path(os.environ["KALTSIT_PREVIOUS_SHARE"]))
    lock_before = theme.ini_entries(theme.read_text(controller.config / "kscreenlockerrc"))
    assert old.apply()["result"] == "applied"
    record = controller.state_file.read_bytes()
    status = controller.status()
    assert status["applied_version"] == previous.VERSION and status["upgrade_available"], status
    try:
        controller.apply()
    except theme.ThemeError as error:
        assert "restore" in str(error)
    else:
        raise AssertionError("previous-version backup was not protected")
    assert controller.state_file.read_bytes() == record
    assert controller.restore()["result"] == "restored"
    assert owned() == original
    assert theme.ini_entries(theme.read_text(controller.config / "kscreenlockerrc")) == lock_before
    assert controller.apply()["result"] == "applied"
    lock_applied = theme.ini_entries(theme.read_text(controller.config / "kscreenlockerrc"))
    assert lock_applied[("[Greeter]", "WallpaperPlugin")] == theme.LOCK_WALLPAPER
    assert controller.apply()["result"] == "already-applied"
    assert controller.restore()["result"] == "restored"
    assert owned() == original
    assert theme.ini_entries(theme.read_text(controller.config / "kscreenlockerrc")) == lock_before
    assert os.readlink(local_cursor) == original_target
    results["previous_version"] = previous.VERSION
    results["previous_to_candidate"] = "previous apply; backup protected; restore; candidate apply; repeat; restore"
    results["previous_backup_unchanged"] = True
    results["previous_lock_configuration_restored"] = True

(root / "transaction-probes.json").write_text(json.dumps(results, indent=2) + "\n")
