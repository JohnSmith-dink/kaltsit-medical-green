#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Derive the greeter palette from the existing KDE scheme, without new colors."""
import configparser
import json
from pathlib import Path
import sys

ROLES = {
    'window': ('Colors:Window', 'BackgroundNormal'),
    'view': ('Colors:View', 'BackgroundNormal'),
    'alternate': ('Colors:View', 'BackgroundAlternate'),
    'text': ('Colors:View', 'ForegroundNormal'),
    'secondary': ('Colors:View', 'ForegroundInactive'),
    'negative': ('Colors:View', 'ForegroundNegative'),
    'accent': ('Colors:Button', 'DecorationFocus'),
    'hover': ('Colors:Button', 'DecorationHover'),
    'selected': ('Colors:Selection', 'BackgroundNormal'),
    'selectedText': ('Colors:Selection', 'ForegroundNormal'),
}


def palette(source):
    config = configparser.ConfigParser(interpolation=None)
    with Path(source).open(encoding='utf-8') as stream:
        config.read_file(stream)
    result = {}
    for name, (group, key) in ROLES.items():
        channels = [int(part) for part in config[group][key].split(',')]
        if len(channels) != 3 or any(not 0 <= part <= 255 for part in channels):
            raise ValueError(f'{group}/{key}: expected three 0..255 RGB channels')
        result[name] = '#' + ''.join(f'{part:02x}' for part in channels)
    return result


if __name__ == '__main__':
    values = palette(sys.argv[1])
    Path(sys.argv[2]).write_text('// Generated from the existing KDE scheme.\n' +
                               '\n'.join(f'var {name} = {json.dumps(value)};' for name, value in values.items()) + '\n', encoding='utf-8')
