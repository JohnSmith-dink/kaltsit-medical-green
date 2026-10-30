#!/usr/bin/env python3
"""Offline integrity and accessibility checks for the packaged theme assets.

Run with: python3 -m unittest discover -s tests -p 'test_assets.py' -v
Only the Python standard library is required; no desktop session is accessed.
"""

import configparser
import hashlib
import json
import os
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
            ("plasmarc][Theme", "name"): "default",
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
            self.assertEqual(index[directory]["Type"], "Scalable")
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
