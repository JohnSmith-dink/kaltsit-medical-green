#!/usr/bin/env python3
"""Offline integrity and accessibility checks for the packaged theme assets.

Run with: python3 -m unittest discover -s tests -p 'test_assets.py' -v
Only the Python standard library is required; no desktop session is accessed.
"""

import configparser
import hashlib
import json
import os
import struct
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT / "share"
THEME_ID = "org.xinyan.kaltsit.medicalgreen"
THEME_NAME = "KaltsitMedicalGreen"
LOOK_AND_FEEL = SHARE / "plasma/look-and-feel" / THEME_ID
FRAME_SHA256 = "1427f0b9f220686a1c1b0bb654c1145302a54c9ba0a44d90dcdcbf5317ae2e8b"


def read_ini(path):
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    with path.open(encoding="utf-8") as source:
        config.read_file(source)
    return config


def rgb(value):
    if value.startswith("#"):
        channels = [int(value[index:index + 2], 16) for index in (1, 3, 5)]
    else:
        channels = [int(channel) for channel in value.split(",")]
    if len(channels) != 3 or any(not 0 <= channel <= 255 for channel in channels):
        raise ValueError("Not an RGB color: " + value)
    return [channel / 255 for channel in channels]


def luminance(value):
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in rgb(value)
    ]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(foreground, background):
    dark, light = sorted((luminance(foreground), luminance(background)))
    return (light + 0.05) / (dark + 0.05)


def jpeg_dimensions(data):
    """Read JPEG SOF dimensions without decoding or requiring Pillow."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("Missing JPEG SOI marker")
    offset = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                   0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(data):
        if data[offset] != 0xFF:
            raise ValueError("Invalid JPEG marker")
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            continue
        length = int.from_bytes(data[offset:offset + 2], "big")
        if length < 2 or offset + length > len(data):
            raise ValueError("Truncated JPEG segment")
        if marker in sof_markers:
            if length < 8:
                raise ValueError("Truncated JPEG SOF segment")
            height = int.from_bytes(data[offset + 3:offset + 5], "big")
            width = int.from_bytes(data[offset + 5:offset + 7], "big")
            return width, height
        offset += length
    raise ValueError("No JPEG SOF segment found")


class ThemeAssetTests(unittest.TestCase):
    def test_global_theme_identity_and_defaults(self):
        metadata = json.loads((LOOK_AND_FEEL / "metadata.json").read_text())
        self.assertEqual(metadata["KPackageStructure"], "Plasma/LookAndFeel")
        self.assertEqual(metadata["KPlugin"]["Id"], THEME_ID)
        self.assertEqual(metadata["KPlugin"]["Name[zh_CN]"], "凯尔希 · 医疗白绿")
        defaults = read_ini(LOOK_AND_FEEL / "contents/defaults")
        expected = {
            ("kdeglobals][KDE", "widgetStyle"): "Breeze",
            ("kdeglobals][General", "ColorScheme"): THEME_NAME,
            ("kdeglobals][Icons", "Theme"): THEME_NAME,
            ("plasmarc][Theme", "name"): THEME_NAME,
            ("kcminputrc][Mouse", "cursorTheme"): "Kaltsit-Sihengtu",
            ("kwinrc][org.kde.kdecoration2", "library"): "org.kde.breeze",
            ("kwinrc][org.kde.kdecoration2", "theme"): "Breeze",
        }
        for (group, key), value in expected.items():
            with self.subTest(group=group, key=key):
                self.assertEqual(defaults[group][key], value)
        self.assertFalse((LOOK_AND_FEEL / "contents/layouts").exists())
        self.assertFalse((LOOK_AND_FEEL / "contents/layout.js").exists())

    def test_no_font_shell_scaling_or_layout_overrides(self):
        configurations = [
            read_ini(LOOK_AND_FEEL / "contents/defaults"),
            read_ini(SHARE / "konsole/KaltsitMedicalGreen.profile"),
            read_ini(SHARE / "color-schemes/KaltsitMedicalGreen.colors"),
        ]
        forbidden_tokens = ("font", "command", "shell", "scale", "cursorsize",
                            "keybinding", "layout", "launcher")
        for config in configurations:
            for group in config:
                for key in config[group]:
                    with self.subTest(group=group, key=key):
                        self.assertFalse(any(token in key.lower() for token in forbidden_tokens))
        profile = configurations[1]
        self.assertEqual(profile["General"]["Parent"], "FALLBACK/")
        self.assertEqual(profile["Appearance"]["ColorScheme"], THEME_NAME)
        ghostty = (SHARE / "ghostty/themes/Kaltsit Medical Green").read_text()
        for line in ghostty.splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key = line.split("=", 1)[0].strip().lower()
                self.assertFalse(any(token in key for token in forbidden_tokens), key)

    def test_icon_inheritance_and_svg_integrity(self):
        icon_root = SHARE / "icons"
        theme_root = icon_root / THEME_NAME
        index = read_ini(theme_root / "index.theme")
        self.assertIn("breeze", index["Icon Theme"]["Inherits"].split(","))
        directories = index["Icon Theme"]["Directories"].split(",")
        for directory in directories:
            self.assertTrue((theme_root / directory).is_dir())
            self.assertEqual(index[directory]["Context"], "Places")
            self.assertEqual(index[directory]["Type"], "Scalable" if directory.endswith("scalable") else "Fixed")
        svg_files = list(theme_root.rglob("*.svg"))
        self.assertGreaterEqual(len(svg_files), 15)
        for path in svg_files:
            with self.subTest(svg=path.name):
                svg = ET.parse(path).getroot()
                self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertTrue(svg.get("viewBox"))
        for path in icon_root.rglob("*"):
            if path.is_symlink():
                with self.subTest(link=str(path.relative_to(icon_root))):
                    self.assertTrue(path.exists(), "Broken icon/cursor symlink")
                    self.assertFalse(Path(os.readlink(path)).is_absolute())
                    self.assertTrue(path.resolve().is_relative_to(icon_root.resolve()))

    def test_small_folder_sizes_have_complete_distinct_geometry(self):
        root = SHARE / "icons" / THEME_NAME / "places"
        expected = {p.name for p in (root / "scalable").glob("*.svg")}
        for size in (16, 22, 32):
            actual = {p.name for p in (root / str(size)).glob("*.svg")}
            self.assertEqual(actual, expected)
            for name in actual:
                svg = ET.parse(root / str(size) / name).getroot()
                self.assertEqual(svg.get("viewBox"), f"0 0 {size} {size}")
                self.assertEqual(svg.get("width"), str(size))
                self.assertNotEqual((root / str(size) / name).read_bytes(), (root / "scalable" / name).read_bytes())

    def test_plasma_style_frames_and_fallback(self):
        root = SHARE / "plasma/desktoptheme" / THEME_NAME
        metadata = json.loads((root / "metadata.json").read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], THEME_NAME)
        self.assertEqual(read_ini(root / "plasmarc")["Settings"]["FallbackTheme"], "default")
        pieces = {"center", "top", "bottom", "left", "right", "topleft", "topright", "bottomleft", "bottomright"}
        for name in ("widgets/panel-background", "dialogs/background", "widgets/background", "widgets/tooltip"):
            svg = ET.parse(root / (name + ".svg")).getroot()
            identifiers = [node.get("id") for node in svg.iter() if node.get("id")]
            self.assertEqual(len(identifiers), len(set(identifiers)))
            self.assertTrue(pieces <= set(identifiers))
            self.assertTrue({"mask-"+p for p in pieces} <= set(identifiers))
            self.assertTrue({"shadow-"+p for p in pieces - {"center"}} <= set(identifiers))
            self.assertFalse(any(node.tag.endswith("filter") for node in svg.iter()))
        # Native interaction controls deliberately continue to come from Breeze.
        self.assertFalse((root / "widgets/button.svg").exists())

    def test_pinned_cursor_files_and_aliases(self):
        manifest = json.loads((ROOT / "docs/cursor-source.json").read_text())
        self.assertEqual(manifest["revision"], "7ef139a6210fd8eb03d0296b624d71eaa3120589")
        self.assertEqual(manifest["installed_id"], "Kaltsit-Sihengtu")
        root = SHARE / "icons/Kaltsit-Sihengtu/cursors"
        self.assertEqual({p.name for p in root.iterdir()}, set(manifest["files"]))
        for name, record in manifest["files"].items():
            with self.subTest(cursor=name):
                path = root / name
                if "symlink" in record:
                    self.assertTrue(path.is_symlink())
                    self.assertEqual(os.readlink(path), record["symlink"])
                    self.assertTrue(path.resolve().is_relative_to(root.resolve()))
                else:
                    self.assertFalse(path.is_symlink())
                    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])

    def test_xcursor_sizes_frames_hotspots_and_delays_match_upstream(self):
        root = SHARE / "icons/Kaltsit-Sihengtu"
        report = json.loads((root / "build-report.json").read_text())
        self.assertEqual(report["sizes"], [24, 32, 48, 64, 96])
        for name, cursor in report["cursors"].items():
            with self.subTest(cursor=name):
                data = (root / "cursors" / name).read_bytes()
                magic, header, version, count = struct.unpack_from("<4I", data)
                self.assertEqual((magic, header, version), (0x72756358, 16, 0x10000))
                self.assertEqual(count, len(cursor["images"]))
                images = []
                last_end = header + count*12
                for i in range(count):
                    kind, size, offset = struct.unpack_from("<3I", data, header+i*12)
                    self.assertGreaterEqual(offset, last_end)
                    chunk, image_kind, image_size, image_version, w, h, x, y, delay = struct.unpack_from("<9I", data, offset)
                    self.assertEqual((chunk, kind, image_kind, image_size, image_version), (36, 0xFFFD0002, kind, size, 1))
                    self.assertTrue(0 <= x < w and 0 <= y < h)
                    last_end = offset + chunk + w*h*4
                    self.assertLessEqual(last_end, len(data))
                    images.append(dict(size=size, width=w, height=h, xhot=x, yhot=y, delay_ms=delay))
                self.assertEqual(images, cursor["images"])
                self.assertEqual({image["size"] for image in images}, {24, 32, 48, 64, 96})
                for size in report["sizes"]:
                    frames = [image for image in images if image["size"] == size]
                    self.assertEqual(len(frames), cursor["frames_per_size"])
                    self.assertEqual(sum(image["delay_ms"] for image in frames), cursor["duration_ms"])

    def test_wallpaper_frame_hash_and_dimensions(self):
        metadata_path = SHARE / "wallpapers/KaltsitMedicalGreen/metadata.json"
        metadata = json.loads(metadata_path.read_text())
        self.assertEqual(metadata["KPlugin"]["Id"], THEME_NAME)
        self.assertEqual(metadata["KPackageStructure"], "Wallpaper/Images")
        provenance = json.loads((ROOT / "docs/asset-provenance.json").read_text())
        self.assertEqual(provenance["frame_index_zero_based"], 707)
        self.assertEqual(provenance["frame_sha256"], FRAME_SHA256)
        self.assertEqual(provenance["image_dimensions"], [3840, 2160])
        self.assertEqual(provenance["display_dimensions"], [3120, 2080])
        self.assertEqual(provenance["display_mode"], "preserveAspectCrop")
        image = (metadata_path.parent / "contents/images/3840x2160.jpg").read_bytes()
        self.assertEqual(len(image), provenance["frame_bytes"])
        self.assertEqual(hashlib.sha256(image).hexdigest(), FRAME_SHA256)
        self.assertEqual(jpeg_dimensions(image), (3840, 2160))
        self.assertFalse(any(SHARE.rglob("*.vbg")), "Package must not carry the source video")

    def test_kde_text_contrast(self):
        colors = read_ini(SHARE / "color-schemes/KaltsitMedicalGreen.colors")
        groups = [group for group in colors.sections() if group.startswith("Colors:")]
        self.assertGreaterEqual(len(groups), 8)
        for group in groups:
            for key in ("ForegroundNormal", "ForegroundInactive", "ForegroundLink"):
                with self.subTest(group=group, key=key):
                    self.assertGreaterEqual(contrast(colors[group][key], colors[group]["BackgroundNormal"]), 4.5)

    def test_konsole_complete_palette_and_contrast(self):
        colors = read_ini(SHARE / "konsole/KaltsitMedicalGreen.colorscheme")
        self.assertEqual(colors["General"]["Opacity"], "1")
        self.assertEqual(colors["General"]["Wallpaper"], "")
        for suffix in ("", "Intense", "Faint"):
            background = colors["Background" + suffix]["Color"]
            with self.subTest(foreground="Foreground" + suffix):
                self.assertGreaterEqual(contrast(colors["Foreground" + suffix]["Color"], background), 4.5)
            for index in range(8):
                group = f"Color{index}{suffix}"
                with self.subTest(color=group):
                    self.assertGreaterEqual(contrast(colors[group]["Color"], background), 4.5)

    def test_ghostty_complete_matching_ansi_palette(self):
        entries = {}
        palette = {}
        for line in (SHARE / "ghostty/themes/Kaltsit Medical Green").read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "palette":
                number, color = value.split("=", 1)
                self.assertNotIn(int(number), palette)
                palette[int(number)] = color
            else:
                self.assertNotIn(key, entries)
                entries[key] = value
        self.assertEqual(set(palette), set(range(16)))
        self.assertGreaterEqual(contrast(entries["foreground"], entries["background"]), 4.5)
        self.assertGreaterEqual(contrast(entries["selection-foreground"], entries["selection-background"]), 4.5)
        self.assertGreaterEqual(contrast(entries["cursor-text"], entries["cursor-color"]), 4.5)
        konsole = read_ini(SHARE / "konsole/KaltsitMedicalGreen.colorscheme")
        for index, color in palette.items():
            suffix = "Intense" if index >= 8 else ""
            with self.subTest(color=index):
                self.assertGreaterEqual(contrast(color, entries["background"]), 4.5)
                self.assertEqual(rgb(color), rgb(konsole[f"Color{index % 8}{suffix}"]["Color"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
