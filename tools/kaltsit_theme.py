#!/usr/bin/env python3
"""Explicit, reversible user-session theme switching; installation is passive.

KDE mutators run only for ``apply`` / ``restore``. Configuration snapshots are
private, and rollback changes individual INI keys, not entire configuration
files. Plasma wallpaper changes use its documented desktop scripting API.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


THEME = "org.xinyan.kaltsit.medicalgreen"
VERSION = "1.1.0"
SCHEME = "KaltsitMedicalGreen"
LOCK_WALLPAPER = "org.xinyan.kaltsit.medicalgreen.lock"
CURSOR = "Kaltsit-Sihengtu"
BEGIN = "# BEGIN KALTSIT MEDICAL GREEN (managed by kaltsit-theme)"
END = "# END KALTSIT MEDICAL GREEN"
INI_FILES = (
    "kdeglobals", "plasmarc", "kcminputrc", "kwinrc", "ksplashrc",
    "kscreenlockerrc", "konsolerc", "kcmfonts", "kaccessrc",
    "gtk-3.0/settings.ini", "gtk-4.0/settings.ini",
)
TEXT_FILES = (
    "kdedefaults/package", "gtk-3.0/colors.css", "gtk-4.0/colors.css",
    "gtk-3.0/gtk.css", "gtk-4.0/gtk.css",
)
GTK_SETTINGS = {"gtk-3.0/settings.ini", "gtk-4.0/settings.ini"}
GTK_OWNED_KEYS = {
    ("[Settings]", key) for key in (
        "gtk-theme-name", "gtk-application-prefer-dark-theme",
        "gtk-icon-theme-name", "gtk-cursor-theme-name",
    )
}
GROUP_RE = re.compile(r"^(\[.*\])\s*$")
COMPONENTS = ("core", "cursor", "wallpaper", "lockscreen", "gtk", "ghostty", "konsole")
OPTIONAL_COMPONENTS = COMPONENTS[1:]
COMPONENT_FILES = {
    "core": {"kdeglobals", "plasmarc", "kwinrc", "kdedefaults/package"},
    "cursor": {"kcminputrc"},
    "wallpaper": {"plasma-org.kde.plasma.desktop-appletsrc"},
    "lockscreen": {"kscreenlockerrc"},
    "gtk": {name for name in INI_FILES + TEXT_FILES if name.startswith("gtk-")},
    "ghostty": set(),
    "konsole": {"konsolerc"},
}


class ThemeError(RuntimeError):
    pass


def read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8", errors="surrogateescape") if path.exists() else None


def atomic_text(path: Path, text: str) -> None:
    """Do not silently break Home Manager or other managed symlinks."""
    if path.is_symlink():
        raise ThemeError(f"配置由符号链接管理，未覆盖：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, name = tempfile.mkstemp(prefix=".kaltsit-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def ini_entries(text: str | None) -> dict[tuple[str, str], str]:
    """Keep raw KConfig groups, key flags and escaped values intact."""
    result = {}
    group = ""
    for line in (text or "").splitlines():
        match = GROUP_RE.match(line.strip())
        if match:
            group = match.group(1)
        elif line.strip() and not line.lstrip().startswith(("#", ";")) and "=" in line:
            key, value = line.split("=", 1)
            result[(group, key.strip())] = value
    return result


def edit_ini(text: str | None, updates: dict[tuple[str, str], str | None]) -> str:
    """Patch only requested keys, retaining comments and unrelated entries."""
    lines = (text or "").splitlines(keepends=True)
    group = ""
    remaining = dict(updates)
    output = []

    def flush(section: str) -> None:
        for identity in list(remaining):
            if identity[0] == section:
                value = remaining.pop(identity)
                if value is not None:
                    if output and not output[-1].endswith("\n"):
                        output[-1] += "\n"
                    output.append(f"{identity[1]}={value}\n")

    for line in lines:
        match = GROUP_RE.match(line.strip())
        if match:
            flush(group)
            group = match.group(1)
            output.append(line)
            continue
        identity = None
        if line.strip() and not line.lstrip().startswith(("#", ";")) and "=" in line:
            identity = (group, line.split("=", 1)[0].strip())
        if identity in updates:
            if identity in remaining:
                value = remaining.pop(identity)
                if value is not None:
                    output.append(f"{identity[1]}={value}\n")
            continue
        output.append(line)
    flush(group)
    for section in dict.fromkeys(key[0] for key in remaining):
        if not any(key[0] == section and value is not None for key, value in remaining.items()):
            continue
        if output and not output[-1].endswith("\n"):
            output[-1] += "\n"
        if section:
            output.append(f"\n{section}\n")
        flush(section)
    return "".join(output)


def preserved_key(key: str) -> bool:
    name = key.lower().replace("-", "").split("[")[0]
    return "font" in name or "scale" in name or "dpi" in name or name in {
        "fixed", "cursorsize", "cursorthemesize", "gtkcursorthemesize",
    }


class Backend:
    def __init__(self, env: dict[str, str], runner=None):
        self.env = env
        self.runner = runner or subprocess.run
        self.suppress_gtk_notifications = False

    def missing_commands(self, commands) -> list[str]:
        # Injected runners are an explicit test boundary, with no host PATH.
        if self.runner is not subprocess.run:
            return []
        return sorted(name for name in set(commands) if shutil.which(name, path=self.env.get("PATH")) is None)

    def should_notify(self, name: str, group: str, key: str | None = None) -> bool:
        # This identity is descriptive: the controller already applies each
        # owned component. Broadcasting it makes kde-gtk-config apply *all*
        # settings, including unrelated GTK fonts after our preserve pass.
        # Native widgets still receive the explicit global style refresh.
        if (name, group, key) == ("kdeglobals", "[KDE]", "LookAndFeelPackage"):
            return False
        # kde-gtk-config subscribes to these KConfigWatcher groups. Suppressing
        # their notifications avoids indirect GTK file writes when GTK is
        # skipped. Qt/Plasma still receive KGlobalSettings signals and KWin's
        # explicit reconfigure. This does not disable or reconfigure kded.
        if not self.suppress_gtk_notifications:
            return True
        return not (name in {"kdeglobals", "kwinrc", "kcminputrc", "breezerc", "kcmfonts"}
                    or name.startswith("gtk-"))

    def run(self, *args: str) -> str:
        try:
            result = self.runner(list(args), env=self.env, check=True, text=True,
                                 capture_output=True, timeout=45)
        except (OSError, subprocess.SubprocessError) as error:
            detail = getattr(error, "stderr", None) or str(error)
            raise ThemeError(f"命令失败 {args[0]}：{detail.strip()}") from error
        return result.stdout.strip()

    def script(self, code: str) -> str:
        return self.run("qdbus", "org.kde.plasmashell", "/PlasmaShell",
                        "org.kde.PlasmaShell.evaluateScript", code)

    def wallpapers(self) -> list[dict]:
        output = self.script("""// kaltsit:snapshot
var result = [];
var all = desktops();
for (var i = 0; i < all.length; ++i) {
    var d = all[i];
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    result.push({id: d.id, plugin: d.wallpaperPlugin,
                 image_exists: d.configKeys.indexOf("Image") !== -1,
                 image: d.readConfig("Image", ""),
                 fill_mode_exists: d.configKeys.indexOf("FillMode") !== -1,
                 fill_mode: d.readConfig("FillMode", 2)});
}
print(JSON.stringify(result));
""")
        try:
            result = json.loads(output)
            if not isinstance(result, list) or not result:
                raise ValueError("no desktops")
            for item in result:
                if not isinstance(item["id"], int) or not isinstance(item["plugin"], str):
                    raise ValueError("invalid desktop")
            return result
        except (ValueError, KeyError, TypeError) as error:
            raise ThemeError("无法读取 Plasma 桌面；请在已登录的 KDE 会话中执行。") from error

    def set_wallpapers(self, items: list[dict]) -> None:
        self.script("// kaltsit:set-wallpapers\nvar saved = " + json.dumps(items) + ";\n" + """
for (var i = 0; i < saved.length; ++i) {
    var s = saved[i];
    var d = desktopById(s.id);
    if (!d) { continue; }
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    function restoreEntry(key, exists, value) {
        if (exists) {
            d.writeConfig(key, value);
            return;
        }
        var c = ConfigFile("plasma-org.kde.plasma.desktop-appletsrc", "Containments");
        c = ConfigFile(c, String(s.id));
        c = ConfigFile(c, "Wallpaper");
        c = ConfigFile(c, "org.kde.image");
        c = ConfigFile(c, "General");
        c.deleteEntry(key);
    }
    restoreEntry("Image", s.image_exists, s.image);
    restoreEntry("FillMode", s.fill_mode_exists, s.fill_mode);
    d.wallpaperPlugin = s.plugin;
    d.reloadConfig();
}
""")

    def key_args(self, path: Path, group: str) -> list[str]:
        # KConfig suppresses Notify for absolute config names. Locate the file
        # with XDG_CONFIG_HOME, but keep its name relative for KConfigWatcher.
        root = Path(self.env["XDG_CONFIG_HOME"])
        try:
            relative = path.relative_to(root)
        except ValueError as error:
            raise ThemeError(f"配置不在 XDG_CONFIG_HOME 内：{path}") from error
        args = ["kwriteconfig6", "--file", str(relative)]
        for part in re.findall(r"\[([^\]]+)\]", group):
            args += ["--group", part]
        return args

    def write_key(self, path: Path, group: str, key: str, value: str) -> None:
        args = self.key_args(path, group)
        notify = ["--notify"] if self.should_notify(str(path.relative_to(self.env["XDG_CONFIG_HOME"])), group, key) else []
        self.run(*args, "--key", key, *notify, value)

    def delete_key(self, path: Path, group: str, key: str) -> None:
        notify = ["--notify"] if self.should_notify(str(path.relative_to(self.env["XDG_CONFIG_HOME"])), group, key) else []
        self.run(*self.key_args(path, group), "--key", key, *notify, "--delete")

    def notify_configs(self, before: dict, after: dict) -> list[str]:
        """Notify actual key changes, including removed keys, after raw patches.

        KDE KConfigWatcher uses ConfigChanged(a{saay}): group names joined by
        U+001D map to lists of UTF-8 key byte arrays. This is intentionally not
        a same-value kwriteconfig call: those need not mark a key dirty.
        See KDE/kconfig src/core/{kconfigwatcher.cpp,dbussanitizer_p.h}.
        """
        warnings = []
        for name in sorted(set(before) | set(after)):
            if name in TEXT_FILES:
                continue
            old = ini_entries(before.get(name))
            new = ini_entries(after.get(name))
            groups = {}
            for group, key in sorted(set(old) | set(new)):
                if old.get((group, key)) != new.get((group, key)) and self.should_notify(name, group, key):
                    nested = "\x1d".join(re.findall(r"\[([^\]]+)\]", group))
                    groups.setdefault(nested, []).append(key.encode("utf-8"))
            if not groups:
                continue
            obj = re.sub(r"[^A-Za-z0-9_/]", "_", "/" + name)
            args = ["busctl", "--user", "emit", obj, "org.kde.kconfig.notify",
                    "ConfigChanged", "a{saay}", str(len(groups))]
            for group, keys in groups.items():
                args += [group, str(len(keys))]
                for key in keys:
                    args += [str(len(key)), *(str(byte) for byte in key)]
            try:
                self.run(*args)
            except ThemeError as error:
                warnings.append(str(error))
        return warnings

    def refresh(self) -> list[str]:
        warnings = []
        commands = [("qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure")]
        for change in (0, 1, 2, 4, 5):
            commands.append(("dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                             "org.kde.KGlobalSettings.notifyChange", f"int32:{change}", "int32:0"))
        for command in commands:
            try:
                self.run(*command)
            except ThemeError as error:
                warnings.append(str(error))
        return warnings

    def refresh_cursor(self) -> None:
        self.run("dbus-send", "--session", "--type=signal", "/KGlobalSettings",
                 "org.kde.KGlobalSettings.notifyChange", "int32:5", "int32:0")
        # Wait for KWin's event loop before another cursor ID is written, so
        # a temporary fallback cannot be coalesced with the final theme.
        self.run("qdbus", "org.kde.KWin", "/KWin", "org.freedesktop.DBus.Peer.Ping")

    def settle_gtk(self, config: Path) -> None:
        """Wait for KDE's delayed CSS export, without changing daemon settings.

        kde-gtk-config 6.6 setColors() defers its write with a 200 ms Qt timer.
        A DBus reply alone therefore is not a completion barrier. First drain
        the daemon's incoming notifications, then require a 250 ms unchanged
        file window and a second daemon barrier. The three-second bound turns
        concurrent, continuous changes into a recoverable error.
        """
        if self.runner is not subprocess.run:
            return
        owner = self.run("qdbus", "org.freedesktop.DBus", "/org/freedesktop/DBus",
                         "org.freedesktop.DBus.NameHasOwner", "org.kde.GtkConfig")
        if owner != "true":
            return
        def barrier():
            self.run("qdbus", "org.kde.GtkConfig", "/GtkConfig", "org.freedesktop.DBus.Peer.Ping")
        def contents():
            return tuple(read_text(config / name) for name in sorted(COMPONENT_FILES["gtk"]))
        barrier()
        previous = contents()
        stable_since = time.monotonic()
        deadline = stable_since + 3
        while time.monotonic() < deadline:
            time.sleep(0.05)
            current = contents()
            if current != previous:
                previous, stable_since = current, time.monotonic()
            if time.monotonic() - stable_since >= 0.25:
                barrier()
                current = contents()
                if current == previous:
                    return
                previous, stable_since = current, time.monotonic()
        raise ThemeError("GTK 同步仍在变更配置，未取得稳定恢复快照；请稍后重试。")


class Controller:
    def __init__(self, data_dir: Path, env=None, backend=None):
        self.env = dict(os.environ if env is None else env)
        home = Path(self.env["HOME"])
        if not home.is_absolute():
            raise ThemeError("HOME 必须是绝对路径，未修改配置。")

        def xdg_directory(name: str, fallback: str) -> Path:
            value = self.env.get(name)
            # The XDG specification treats empty and relative paths as unset.
            return Path(value) if value and Path(value).is_absolute() else home / fallback

        self.config = xdg_directory("XDG_CONFIG_HOME", ".config")
        self.data = xdg_directory("XDG_DATA_HOME", ".local/share")
        state_home = xdg_directory("XDG_STATE_HOME", ".local/state")
        self.state_dir = state_home / "kaltsit-theme"
        self.state_file = self.state_dir / "active.json"
        self.share = data_dir.resolve()
        self.env["XDG_CONFIG_HOME"] = str(self.config)
        self.env["XDG_DATA_HOME"] = str(self.data)
        self.env["XDG_STATE_HOME"] = str(state_home)
        self.env["XDG_DATA_DIRS"] = str(self.share) + ":" + (self.env.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share")
        self.backend = backend or Backend(self.env)
        self.backend.env = self.env

    def snapshot(self, components=None) -> dict[str, str | None]:
        names = set(INI_FILES + TEXT_FILES)
        defaults = self.config / "kdedefaults"
        if defaults.is_dir():
            names.update(str(p.relative_to(self.config)) for p in defaults.rglob("*") if p.is_file())
        if components is not None:
            owned = set().union(*(COMPONENT_FILES[c] for c in components))
            names &= owned
        return {name: read_text(self.config / name) for name in sorted(names)}

    def save(self, state: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state_dir, 0o700)
        atomic_text(self.state_file, json.dumps(state, indent=2, ensure_ascii=True) + "\n")

    def load(self) -> dict | None:
        text = read_text(self.state_file)
        if text is None:
            return None
        state = json.loads(text)
        if state.get("version") not in (1, 2, 3) or state.get("theme") != THEME:
            raise ThemeError(f"无法识别恢复记录：{self.state_file}")
        return state

    @contextlib.contextmanager
    def lock(self):
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.state_dir / "lock").open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ThemeError("另一个主题切换命令正在执行。") from error
            yield

    def terminal_blocks(self, before: dict, components=None) -> list[dict]:
        components = COMPONENTS if components is None else components
        old_profile = ini_entries(before.get("konsolerc")).get(("[Desktop Entry]", "DefaultProfile"), "FALLBACK/")
        # Never make a self-referencing inheritance chain on a second install.
        if Path(old_profile).name == f"{SCHEME}.profile":
            old_profile = "FALLBACK/"
        ghostty = self.config / "ghostty/config.ghostty"
        if not ghostty.exists() and not ghostty.is_symlink():
            ghostty = self.config / "ghostty/config"
        targets = [
            ("ghostty", ghostty, f"config-file = {self.state_dir / 'ghostty.conf'}\n"),
            ("konsole", self.data / f"konsole/{SCHEME}.profile",
             f"[General]\nName=Kal'tsit Medical Green\nParent={old_profile}\n"
             f"\n[Appearance]\nColorScheme={SCHEME}\n"),
        ]
        result = []
        for component, path, content in targets:
            if component not in components:
                continue
            previous = read_text(path)
            if path.is_symlink():
                raise ThemeError(f"终端配置由符号链接管理，未覆盖：{path}")
            if BEGIN in (previous or "") or END in (previous or ""):
                raise ThemeError(f"发现没有对应恢复记录的主题标记块：{path}")
            prefix = "" if previous is None or previous.endswith("\n") else "\n"
            block = prefix + BEGIN + "\n" + content + END + "\n"
            result.append({"component": component, "path": str(path), "block": block, "existed": previous is not None,
                           "added_separator": bool(prefix)})
        return result

    def preserve_settings(self, before: dict) -> list[str]:
        after = {name: read_text(self.config / name) for name in before}
        for name in set(before) | set(after):
            if name in TEXT_FILES:
                continue
            old = ini_entries(before.get(name))
            new = ini_entries(after.get(name))
            updates = {key: old.get(key) for key in set(old) | set(new)
                       if preserved_key(key[1]) and old.get(key) != new.get(key)}
            if updates:
                atomic_text(self.config / name, edit_ini(after.get(name), updates))
        return self.backend.notify_configs(after, {name: read_text(self.config / name) for name in before})

    def cursor_overrides(self) -> list[dict]:
        """Old per-user copies shadow Nix's identically named cursor theme.

        Move only existing copies to the private transaction directory. This
        does not link configuration files or replace unrelated icon themes.
        """
        result = []
        target = self.share / "icons" / CURSOR
        paths = dict.fromkeys((Path(self.env["HOME"]) / ".icons" / CURSOR,
                               self.data / "icons" / CURSOR))
        seen = set()
        for path in paths:
            identity = path.parent.resolve() / path.name
            if identity in seen:
                continue
            seen.add(identity)
            if not path.exists() and not path.is_symlink():
                continue
            if path.resolve() == target.resolve():
                continue
            if not target.is_dir():
                raise ThemeError(f"缺少新指针资源：{target}")
            if not path.is_dir() and not path.is_symlink():
                raise ThemeError(f"指针主题路径不是目录：{path}")
            backup = self.state_dir / f"cursor-backup-{len(result)}"
            if backup.exists() or backup.is_symlink():
                raise ThemeError(f"发现尚未恢复的指针目录：{backup}")
            ancestor = self.state_dir
            while not ancestor.exists():
                ancestor = ancestor.parent
            if path.lstat().st_dev != ancestor.stat().st_dev:
                raise ThemeError("指针目录与恢复目录不在同一文件系统，无法安全原子备份，未切换主题。")
            result.append({"path": str(path), "backup": str(backup), "target": str(target),
                           "parent": str(path.parent.resolve())})
        return result

    def install_cursor_overrides(self, state: dict) -> None:
        for item in state["cursor_overrides"]:
            path = Path(item["path"])
            path.rename(item["backup"])
            path.symlink_to(item["target"], target_is_directory=True)

    def restore_cursor_overrides(self, state: dict) -> list[str]:
        warnings = []
        for item in state.get("cursor_overrides", []):
            path, backup = Path(item["path"]), Path(item["backup"])
            legacy_home_alias = (path.parent == Path(self.env["HOME"]) / ".icons"
                                 and path.parent.resolve() == self.data / "icons"
                                 and self.managed_path(self.data / "icons") is None)
            parent_changed = (str(path.parent.resolve()) != item["parent"] if "parent" in item
                              else self.managed_path(path.parent) is not None and not legacy_home_alias)
            if parent_changed:
                warnings.append(f"保留切换后改变的指针父目录，原资源仍在 {backup}：{path.parent}")
                continue
            ours = path.is_symlink() and os.readlink(path) == item["target"]
            has_backup = backup.exists() or backup.is_symlink()
            if not has_backup:
                if ours:
                    warnings.append(f"指针备份缺失，保留当前资源链接：{path}")
                continue
            if path.exists() or path.is_symlink():
                if not ours:
                    warnings.append(f"保留切换后修改的指针目录，原目录仍在 {backup}：{path}")
                    continue
                path.unlink()
            backup.rename(path)
        return warnings

    def managed_path(self, path: Path) -> Path | None:
        """Treat a symlinked config directory as managed, not just leaf links."""
        roots = {self.config.parent, self.data.parent, Path(self.env["HOME"]).parent}
        current = path
        while current not in roots and current != current.parent:
            if current.is_symlink():
                return current
            current = current.parent
        return None

    def requested_options(self, skip=(), wallpaper=None) -> dict:
        if isinstance(skip, str):
            skip = (skip,)
        unknown = set(skip) - set(OPTIONAL_COMPONENTS)
        if unknown:
            raise ThemeError("不支持跳过组件：" + ", ".join(sorted(unknown)))
        custom = None
        if wallpaper is not None:
            path = Path(wallpaper)
            if not path.is_absolute():
                raise ThemeError("自定义壁纸必须使用绝对路径，未修改配置。")
            path = path.resolve()
            if not path.is_file():
                raise ThemeError(f"自定义壁纸不存在或不是文件：{path}")
            try:
                from PIL import Image
            except ImportError as error:
                raise ThemeError("缺少 Pillow 图片验证依赖，未修改配置。") from error
            try:
                with Image.open(path) as picture:
                    picture.verify()
                with Image.open(path) as picture:
                    if picture.width < 1 or picture.height < 1:
                        raise ValueError("empty image")
                    picture.load()
            except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as error:
                raise ThemeError(f"无法读取自定义壁纸图片：{path} ({error})") from error
            custom = str(path)
        return {"skip": sorted(set(skip)), "wallpaper": custom}

    def required_commands(self, enabled) -> set[str]:
        commands = {"kwriteconfig6", "qdbus", "busctl", "dbus-send"}
        if "cursor" in enabled:
            commands.add("kreadconfig6")
            if "gtk" in enabled:
                commands.add("plasma-apply-cursortheme")
        if "gtk" in enabled:
            commands.add("plasma-apply-colorscheme")
        return commands

    def _prepare(self, options: dict, dry_run=False) -> dict:
        components = {name: {"status": "planned"} for name in COMPONENTS}
        for name in options["skip"]:
            components[name] = {"status": "skipped", "reason": "用户通过 --skip 跳过"}
        ghostty = self.config / "ghostty/config.ghostty"
        if not ghostty.exists() and not ghostty.is_symlink():
            ghostty = self.config / "ghostty/config"
        paths = {name: [self.config / relative for relative in sorted(files)]
                 for name, files in COMPONENT_FILES.items()}
        paths["ghostty"] = [ghostty]
        paths["konsole"].append(self.data / f"konsole/{SCHEME}.profile")
        for name in COMPONENTS:
            if components[name]["status"] == "skipped":
                continue
            managed = next((link for path in paths[name] if (link := self.managed_path(path))), None)
            if managed:
                if name == "core":
                    raise ThemeError(f"核心配置由符号链接管理，未修改任何设置：{managed}")
                components[name] = {"status": "skipped", "reason": f"配置由符号链接管理：{managed}"}
        enabled = [name for name, item in components.items() if item["status"] != "skipped"]
        wallpaper = Path(options["wallpaper"]) if options["wallpaper"] else self.share / f"wallpapers/{SCHEME}/contents/images/3840x2160.jpg"
        if {"wallpaper", "lockscreen"} & set(enabled) and not wallpaper.is_file():
            raise ThemeError(f"缺少壁纸：{wallpaper}")
        if "lockscreen" in enabled:
            lock_plugin = self.share / "plasma/wallpapers" / LOCK_WALLPAPER
            if not all((lock_plugin / name).is_file() for name in ("metadata.json", "contents/ui/main.qml", "contents/config/main.xml")):
                raise ThemeError(f"缺少锁屏壁纸资源，未修改配置：{lock_plugin}")
            lock_shell = self.share / "plasma/shells/org.kde.plasma.desktop"
            if not all((lock_shell / name).is_file() for name in (
                "metadata.json", "contents/lockscreen/LockScreen.qml",
                "contents/lockscreen/LockScreenUi.qml", "contents/lockscreen/KaltsitWallpaperFader.qml",
            )):
                raise ThemeError("缺少锁屏原色适配资源，请使用完整 Nix 构建包；未修改配置")
        before = self.snapshot(enabled)
        blocks = self.terminal_blocks(before, enabled)
        missing = self.backend.missing_commands(self.required_commands(enabled))
        if missing and not dry_run:
            raise ThemeError("缺少所需命令：" + ", ".join(missing) + "。请安装运行依赖，并在已登录的 KDE Plasma 会话中执行。")
        if not dry_run and "gtk" in enabled:
            # A previous controller/version may have returned while kded still
            # had a delayed export pending. Back up its completed state.
            self.backend.settle_gtk(self.config)
            before = self.snapshot(enabled)
            blocks = self.terminal_blocks(before, enabled)
        scheme_path = self.share / f"color-schemes/{SCHEME}.colors"
        scheme = ini_entries(read_text(scheme_path))
        if not scheme:
            raise ThemeError(f"缺少配色文件：{scheme_path}")
        updates = []
        def add(component, name, group, key, value):
            updates.append({"component": component, "file": name, "group": group, "key": key,
                            "old": ini_entries(before.get(name)).get((group, key)), "new": value})
        add("core", "kdeglobals", "[General]", "AccentColor", "0,0,0,0")
        add("core", "kdeglobals", "[General]", "accentColorFromWallpaper", "false")
        # Write only authored defaults. plasma-apply-lookandfeel also applies
        # the cursor and other optional components and therefore is not used.
        for name, group, key, value in (
            ("kdeglobals", "[KDE]", "LookAndFeelPackage", THEME),
            ("kdeglobals", "[KDE]", "widgetStyle", "Breeze"),
            ("kdeglobals", "[Icons]", "Theme", SCHEME),
            ("plasmarc", "[Theme]", "name", SCHEME),
            ("kwinrc", "[org.kde.kdecoration2]", "library", "org.kde.breeze"),
            ("kwinrc", "[org.kde.kdecoration2]", "theme", "Breeze"),
        ):
            add("core", name, group, key, value)
        for (group, key), value in scheme.items():
            if (group.startswith(("[Colors:", "[ColorEffects:", "[WM]"))
                    or (group, key) in {("[General]", "ColorScheme"), ("[General]", "shadeSortColumn"), ("[KDE]", "contrast")}):
                add("core", "kdeglobals", group, key, value)
        cursor = None
        diagnostics = []
        if "cursor" in enabled:
            if "kreadconfig6" not in missing:
                size = self.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorSize", "--default", self.env.get("XCURSOR_SIZE", "24"))
                name = self.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", "--default", self.env.get("XCURSOR_THEME", "breeze_cursors"))
                if not size.isdigit():
                    raise ThemeError("无法读取当前光标尺寸，未切换主题。")
                cursor = {"theme": name, "size": size}
            add("cursor", "kcminputrc", "[Mouse]", "cursorTheme", CURSOR)
        if "lockscreen" in enabled:
            add("lockscreen", "kscreenlockerrc", "[Greeter]", "WallpaperPlugin", LOCK_WALLPAPER)
            add("lockscreen", "kscreenlockerrc", f"[Greeter][Wallpaper][{LOCK_WALLPAPER}][General]", "Image", wallpaper.as_uri())
            add("lockscreen", "kscreenlockerrc", f"[Greeter][Wallpaper][{LOCK_WALLPAPER}][General]", "FillMode", "2")
        if "gtk" in enabled:
            for version in (3, 4):
                for key, value in (("gtk-theme-name", "Breeze"), ("gtk-application-prefer-dark-theme", "false"), ("gtk-icon-theme-name", SCHEME)):
                    add("gtk", f"gtk-{version}.0/settings.ini", "[Settings]", key, value)
                if "cursor" in enabled:
                    add("gtk", f"gtk-{version}.0/settings.ini", "[Settings]", "gtk-cursor-theme-name", CURSOR)
        if "konsole" in enabled:
            add("konsole", "konsolerc", "[Desktop Entry]", "DefaultProfile", f"{SCHEME}.profile")
        wallpapers = []
        if "qdbus" not in missing:
            try:
                self.backend.run("qdbus", "org.kde.KWin", "/KWin", "org.freedesktop.DBus.Peer.Ping")
                if "wallpaper" in enabled:
                    wallpapers = self.backend.wallpapers()
            except ThemeError as error:
                if not dry_run:
                    raise ThemeError(f"无法访问 KDE Plasma 会话，未修改配置：{error}") from error
                diagnostics.append(str(error))
        overrides = self.cursor_overrides() if "cursor" in enabled else []
        themed = [dict(item, plugin="org.kde.image", image_exists=True, image=wallpaper.as_uri(), fill_mode_exists=True, fill_mode=2) for item in wallpapers]
        file_actions = [{"component": "core", "path": str(self.config / "kdedefaults/package"), "action": "write", "old": before.get("kdedefaults/package"), "new": THEME + "\n"}]
        for block in blocks:
            file_actions.append({"component": block["component"], "path": block["path"], "action": "append-managed-block", "new": block["block"]})
        for item in overrides:
            file_actions.append(dict(item, component="cursor", action="backup-and-link"))
        return {"result": "dry-run", "components": components, "request_options": options,
                "changes": updates, "file_actions": file_actions,
                "wallpaper_changes": [{"old": old, "new": new} for old, new in zip(wallpapers, themed)],
                "missing_commands": missing, "diagnostics": diagnostics,
                "_before": before, "_blocks": blocks, "_cursor": cursor,
                "_overrides": overrides, "_wallpapers": wallpapers, "_themed": themed}

    def plan(self, skip=(), wallpaper=None) -> dict:
        plan = self._prepare(self.requested_options(skip, wallpaper), dry_run=True)
        return {key: value for key, value in plan.items() if not key.startswith("_")}

    def existing_application(self, options) -> dict | None:
        existing = self.load()
        if existing:
            if existing.get("phase") != "active":
                raise ThemeError("发现未完成的切换记录，请先执行 kaltsit-theme restore。")
            if existing.get("theme_version", "1.0.0") != VERSION:
                raise ThemeError("发现旧版本的已应用记录，备份保持不变。请先执行 kaltsit-theme restore，再执行 kaltsit-theme apply 升级。")
            if existing.get("request_options", {"skip": [], "wallpaper": None}) != options:
                raise ThemeError("组件选择或壁纸参数已改变，原备份保持不变。请先执行 kaltsit-theme restore，再重新 apply。")
            return {"result": "already-applied", "state": str(self.state_file), "components": self.state_components(existing)}
        return None

    def apply(self, skip=(), dry_run=False, wallpaper=None) -> dict:
        options = self.requested_options(skip, wallpaper)
        existing = self.existing_application(options)
        if existing:
            return dict(existing, dry_run=True) if dry_run else existing
        if dry_run:
            return self.plan(skip, wallpaper)
        # All validation precedes lock/state creation. A rejected core or invalid
        # image therefore leaves even the recovery directory untouched.
        plan = self._prepare(options)
        with self.lock():
            existing = self.existing_application(options)
            if existing:
                return existing
            # Another controller may have completed a restore between the
            # read-only preflight and flock. Capture its finished baseline,
            # never a stale intermediate snapshot from before the lock.
            plan = self._prepare(options)
            components = {name: dict(item, status="applied") if item["status"] == "planned" else item
                          for name, item in plan["components"].items()}
            enabled = {name for name, item in components.items() if item["status"] == "applied"}
            # Batch watcher notifications after the entire palette is on disk.
            # Per-key notifications let kded export a mixture of old/new roles.
            self.backend.suppress_gtk_notifications = True
            before = plan["_before"]
            state = {"version": 3, "theme": THEME, "theme_version": VERSION,
                     "phase": "applying", "before": before, "components": components,
                     "request_options": options, "wallpapers_before": plan["_wallpapers"],
                     "blocks": plan["_blocks"], "cursor_before": plan["_cursor"],
                     "cursor_overrides": plan["_overrides"]}
            self.save(state)
            try:
                self.install_cursor_overrides(state)
                # All writes are planned and component-scoped. No global-theme
                # application tool can accidentally re-enable skipped features.
                for change in plan["changes"]:
                    self.backend.write_key(self.config / change["file"], change["group"], change["key"], change["new"])
                atomic_text(self.config / "kdedefaults/package", THEME + "\n")
                if "gtk" in enabled:
                    # GTK export is intentionally confined to the GTK component.
                    self.backend.run("plasma-apply-colorscheme", "--accent-color", "transparent")
                if "cursor" in enabled and "gtk" in enabled:
                    cursor = state["cursor_before"]
                    # The planned value is already on disk, so first restore the
                    # original key silently for the live tool's unchanged guard.
                    self.backend.write_key(self.config / "kcminputrc", "[Mouse]", "cursorTheme", cursor["theme"])
                    if cursor["theme"] == CURSOR:
                        self.backend.run("plasma-apply-cursortheme", "--size", cursor["size"], "breeze_cursors")
                    self.backend.run("plasma-apply-cursortheme", "--size", cursor["size"], CURSOR)
                elif "cursor" in enabled:
                    if state["cursor_before"]["theme"] == CURSOR:
                        self.backend.write_key(self.config / "kcminputrc", "[Mouse]", "cursorTheme", "breeze_cursors")
                        self.backend.refresh_cursor()
                        self.backend.write_key(self.config / "kcminputrc", "[Mouse]", "cursorTheme", CURSOR)
                    self.backend.refresh_cursor()
                if "wallpaper" in enabled:
                    state["wallpapers_after"] = plan["_themed"]
                    self.save(state)
                    self.backend.set_wallpapers(plan["_themed"])
                if "ghostty" in enabled:
                    atomic_text(self.state_dir / "ghostty.conf", f"theme = {self.share / 'ghostty/themes/Kaltsit Medical Green'}\n")
                for block in state["blocks"]:
                    path = Path(block["path"])
                    atomic_text(path, (read_text(path) or "") + block["block"])
                warnings = self.preserve_settings(before)
                self.backend.suppress_gtk_notifications = "gtk" not in enabled
                warnings.extend(self.backend.notify_configs(before, self.snapshot(enabled)))
                warnings.extend(self.backend.refresh())
                if "gtk" in enabled:
                    self.backend.settle_gtk(self.config)
                state["after"] = self.snapshot(enabled)
                state["phase"] = "active"
                self.save(state)
                return {"result": "applied" if len(enabled) == len(COMPONENTS) else "partially-applied",
                        "state": str(self.state_file), "components": components, "warnings": warnings,
                        "note": "终端配色对新建窗口生效；字体、缩放、光标尺寸和桌面布局保留。"}
            except BaseException as error:
                state["after"] = self.snapshot(enabled)
                state["phase"] = "failed"
                self.save(state)
                try:
                    result = self._restore(state, force=True)
                except BaseException as rollback_error:
                    raise ThemeError(f"应用失败：{error}；自动恢复未完成：{rollback_error}。请运行 restore。") from error
                suffix = "已自动恢复。" if result["result"] == "restored" else "自动恢复有未完成项，请运行 restore。"
                raise ThemeError(f"应用失败：{error}；{suffix}") from error
            finally:
                self.backend.suppress_gtk_notifications = False

    @staticmethod
    def state_components(state) -> dict:
        if not state:
            return {name: {"status": "not-applied"} for name in COMPONENTS}
        if state.get("version", 1) < 3:
            return {name: {"status": "applied"} for name in COMPONENTS}
        return state["components"]

    def restore_files(self, state: dict, force: bool = False) -> list[str]:
        warnings = []
        before, after = state["before"], state.get("after", self.snapshot())
        for name in sorted(set(before) | set(after)):
            old, applied = before.get(name), after.get(name)
            if old == applied:
                continue
            path = self.config / name
            current = read_text(path)
            if current == old:
                continue
            managed = self.managed_path(path)
            if managed:
                warnings.append(f"保留切换后由符号链接管理的配置：{managed}")
                continue
            if name in TEXT_FILES:
                if current != applied and not force:
                    warnings.append(f"保留切换后修改的文件：{path}")
                elif old is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_text(path, old)
                continue
            old_keys, applied_keys, now_keys = map(ini_entries, (old, applied, current))
            updates = {}
            for key in set(old_keys) | set(applied_keys):
                # kded synchronizes modules, fonts, DPI and other GTK settings
                # asynchronously. They can appear between either snapshot and
                # rollback, and never belong to this theme transaction.
                if name in GTK_SETTINGS and key not in GTK_OWNED_KEYS:
                    continue
                old_value, new_value = old_keys.get(key), applied_keys.get(key)
                if old_value == new_value or now_keys.get(key) == old_value:
                    continue
                if force or now_keys.get(key) == new_value:
                    updates[key] = old_value
                else:
                    warnings.append(f"保留切换后修改的设置：{name} {key[0]} {key[1]}")
            only_owned = name not in GTK_SETTINGS or set(now_keys) <= GTK_OWNED_KEYS
            if old is None and current == applied and only_owned:
                path.unlink(missing_ok=True)
            elif updates:
                atomic_text(path, edit_ini(current, updates))
        return warnings

    def _restore(self, state: dict, force: bool = False) -> dict:
        warnings = []
        enabled = {name for name, item in self.state_components(state).items() if item["status"] == "applied"}
        scoped = enabled if state.get("version", 1) >= 3 else None
        protect_gtk = "gtk" not in enabled or any(
            self.managed_path(self.config / name) for name in COMPONENT_FILES["gtk"])
        if not protect_gtk:
            try:
                self.backend.settle_gtk(self.config)
            except ThemeError as error:
                warnings.append(str(error))
        # Restoring exact CSS/settings must not queue a fresh generated export
        # that overwrites a user's original custom CSS after restore returns.
        # Qt/KWin still refresh via their native global notifications below.
        self.backend.suppress_gtk_notifications = True
        notification_before = self.snapshot(scoped)
        # Restore assets before reloading the original live cursor, including
        # the case where both versions deliberately use the same cursor ID.
        warnings.extend(self.restore_cursor_overrides(state))
        try:
            if "wallpaper" not in enabled:
                raise StopIteration
            if self.managed_path(self.config / "plasma-org.kde.plasma.desktop-appletsrc"):
                raise ThemeError("保留切换后由符号链接管理的桌面壁纸配置。")
            current = {item["id"]: item for item in self.backend.wallpapers()}
            after = {item["id"]: item for item in state.get("wallpapers_after", [])}
            restore = []
            for item in state["wallpapers_before"]:
                now = current.get(item["id"])
                if now is None or now == item:
                    continue
                if force or now == after.get(item["id"]):
                    restore.append(item)
                else:
                    warnings.append(f"保留切换后修改的桌面壁纸：{item['id']}")
            if restore:
                self.backend.set_wallpapers(restore)
        except StopIteration:
            pass
        except ThemeError as error:
            warnings.append(str(error))
        cursor = state.get("cursor_before")
        if cursor and not protect_gtk and not self.managed_path(self.config / "kcminputrc"):
            # Run the live cursor tool while the on-disk theme is still the new
            # one; otherwise it can see the restored value and do nothing.
            cursor_snapshot = self.snapshot(scoped)
            try:
                current_theme = self.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse",
                                                 "--key", "cursorTheme", "--default", cursor["theme"])
                current_size = self.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse",
                                                "--key", "cursorSize", "--default", cursor["size"])
                if force or current_theme in {CURSOR, cursor["theme"]}:
                    if current_theme == cursor["theme"] == CURSOR:
                        self.backend.run("plasma-apply-cursortheme", "--size", current_size, "breeze_cursors")
                    self.backend.run("plasma-apply-cursortheme", "--size", current_size, cursor["theme"])
            except ThemeError as error:
                warnings.append(str(error))
            finally:
                # The cursor helper emits its own KConfig notifications. Drain
                # the resulting GTK cursor/size writes before restoring the
                # exact saved GTK settings (which can intentionally differ).
                try:
                    self.backend.settle_gtk(self.config)
                except ThemeError as error:
                    warnings.append(str(error))
                # Cursor tools can create default-valued keys. Undo only their
                # disk side effects before restoring the original transaction,
                # so originally absent keys remain absent after restoration.
                warnings.extend(self.restore_files({"before": cursor_snapshot, "after": self.snapshot(scoped)}, force=True))
        elif cursor and protect_gtk and not self.managed_path(self.config / "kcminputrc"):
            # Live reload without KConfigWatcher emissions: cursor theme tools
            # emit their own notifications and would overwrite skipped GTK.
            # KConfig may omit a local value equal to an inherited default.
            # Query the effective theme just as the ordinary restore path does.
            try:
                current = self.backend.run("kreadconfig6", "--file", "kcminputrc", "--group", "Mouse",
                                           "--key", "cursorTheme", "--default", cursor["theme"])
            except ThemeError as error:
                warnings.append(str(error))
                current = None
            if current is not None and (force or current in {CURSOR, cursor["theme"]}):
                original_cursor_text = read_text(self.config / "kcminputrc")
                try:
                    if current == cursor["theme"] == CURSOR:
                        self.backend.write_key(self.config / "kcminputrc", "[Mouse]", "cursorTheme", "breeze_cursors")
                        self.backend.refresh_cursor()
                    self.backend.write_key(self.config / "kcminputrc", "[Mouse]", "cursorTheme", cursor["theme"])
                    self.backend.refresh_cursor()
                except ThemeError as error:
                    warnings.append(str(error))
                finally:
                    # Restore the pre-helper disk view before conflict-aware
                    # transaction rollback (the live cursor has already reloaded).
                    if original_cursor_text is None:
                        (self.config / "kcminputrc").unlink(missing_ok=True)
                    else:
                        atomic_text(self.config / "kcminputrc", original_cursor_text)
        warnings.extend(self.restore_files(state, force=force))
        for block in state["blocks"]:
            path = Path(block["path"])
            current = read_text(path)
            if current is None:
                continue
            managed = self.managed_path(path)
            if managed:
                warnings.append(f"保留切换后由符号链接管理的终端配置：{managed}")
                continue
            if block["block"] in current:
                head, tail = current.split(block["block"], 1)
                separator = "\n" if head and tail and block.get("added_separator") else ""
                remaining = head + separator + tail
                if not block["existed"] and not remaining:
                    path.unlink()
                else:
                    atomic_text(path, remaining)
            elif BEGIN in current or END in current:
                warnings.append(f"保留切换后修改的终端主题块：{path}")
        warnings.extend(self.backend.notify_configs(notification_before, self.snapshot(scoped)))
        refresh_warnings = self.backend.refresh()
        self.backend.suppress_gtk_notifications = False
        if warnings:
            state["phase"] = "restore-incomplete"
            self.save(state)
            return {"result": "restore-incomplete", "warnings": warnings + refresh_warnings,
                    "state": str(self.state_file)}
        self.state_file.unlink(missing_ok=True)
        (self.state_dir / "ghostty.conf").unlink(missing_ok=True)
        return {"result": "restored", "warnings": refresh_warnings}

    def restore(self) -> dict:
        with self.lock():
            state = self.load()
            if state is None:
                return {"result": "nothing-to-restore"}
            return self._restore(state, force=state.get("phase") in {"applying", "failed"})

    def effective_entries(self, name: str) -> dict[tuple[str, str], str]:
        """Read the KConfig search hierarchy without tools or a session bus.

        Explicit user keys win over look-and-feel defaults and XDG config
        directories (first directory wins). Immutable/deleted entries retain
        their KConfig meaning instead of being mistaken for literal key names.
        """
        raw_dirs = self.env.get("XDG_CONFIG_DIRS") or "/etc/xdg"
        dirs = [self.config, self.config / "kdedefaults"]
        dirs.extend(Path(value) for value in raw_dirs.split(":") if value and Path(value).is_absolute())
        paths = list(dict.fromkeys(directory / name for directory in dirs))
        result = {}
        locked_keys, locked_groups = set(), set()
        file_locked = False
        for path in reversed(paths):
            if file_locked:
                break
            text = read_text(path)
            new_locked_groups = set()
            for (raw_group, raw_key), value in ini_entries(text).items():
                group_flags = re.findall(r"\[\$([^]]+)\]", raw_group)
                group = re.sub(r"\[\$[^]]+\]", "", raw_group)
                key_flags = re.findall(r"\[\$([^]]+)\]", raw_key)
                key = re.sub(r"\[\$[^]]+\]", "", raw_key)
                identity = (group, key)
                if group in locked_groups or identity in locked_keys:
                    continue
                if any("d" in flags for flags in key_flags):
                    result.pop(identity, None)
                else:
                    if any("e" in flags for flags in key_flags):
                        value = re.sub(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z_0-9]*)",
                                       lambda match: self.env.get(match[1] or match[2], match[0]), value)
                    result[identity] = value
                if any("i" in flags for flags in key_flags):
                    locked_keys.add(identity)
                if any("i" in flags for flags in group_flags):
                    new_locked_groups.add(group)
            locked_groups.update(new_locked_groups)
            file_locked = any(line.strip() == "[$i]" for line in (text or "").splitlines())
        return result

    def status(self) -> dict:
        state = self.load()
        actual = self.effective_entries("kdeglobals")
        get = lambda group, key: actual.get((group, key))
        style = self.effective_entries("plasmarc")
        applied_version = state.get("theme_version", "1.0.0") if state else None
        return {"theme": THEME, "phase": state["phase"] if state else "not-applied",
                "installed_version": VERSION, "applied_version": applied_version,
                "upgrade_available": state is not None and applied_version != VERSION,
                "restore_available": state is not None, "state": str(self.state_file),
                "components": self.state_components(state),
                "missing_commands": self.backend.missing_commands(self.required_commands(
                    [name for name, item in self.state_components(state).items() if item["status"] != "skipped"])),
                "current_plasma_style": style.get(("[Theme]", "name")),
                "current_color_scheme": get("[General]", "ColorScheme"),
                "current_icons": get("[Icons]", "Theme"),
                "current_look_and_feel": get("[KDE]", "LookAndFeelPackage")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="显式应用或恢复凯尔希医疗白绿主题（安装不会自动切换）。")
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("command", choices=("apply", "restore", "status"))
    parser.add_argument("--skip", action="append", choices=OPTIONAL_COMPONENTS, default=[], help="跳过可选组件，可重复指定")
    parser.add_argument("--dry-run", action="store_true", help="只读预演，不创建恢复记录或修改配置")
    parser.add_argument("--wallpaper", type=Path, help="桌面与锁屏使用的自定义图片绝对路径")
    args = parser.parse_args(argv)
    if args.command != "apply" and (args.skip or args.dry_run or args.wallpaper is not None):
        parser.error("--skip、--dry-run 和 --wallpaper 仅适用于 apply")
    try:
        controller = Controller(args.data_dir)
        result = (controller.apply(skip=args.skip, dry_run=args.dry_run, wallpaper=args.wallpaper)
                  if args.command == "apply" else getattr(controller, args.command)())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get("result") == "restore-incomplete" else 0
    except (ThemeError, OSError, ValueError) as error:
        print(f"kaltsit-theme: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
