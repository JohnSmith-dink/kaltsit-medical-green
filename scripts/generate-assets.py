#!/usr/bin/env python3
"""Generate original MIT-licensed SVG assets; Python standard library only.

The Plasma surfaces are real nine-slice frames (no unsupported SVG filters).
Folder geometry and stroke weights are fitted separately at each target size.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "share/plasma/desktoptheme/KaltsitMedicalGreen"
ICONS = ROOT / "share/icons/KaltsitMedicalGreen"
HEADER = '<!-- SPDX-FileCopyrightText: 2026 Xinyan; SPDX-License-Identifier: MIT -->\n'


def surface(radius, margin, shadow):
    r, c, s = radius, 8, shadow
    parts = [HEADER, '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">',
             '<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
             '<stop stop-color="#25352D" stop-opacity="0"/><stop offset="1" stop-color="#25352D" stop-opacity=".16"/>'
             '</linearGradient><radialGradient id="corner" cx="1" cy="1" r="1">'
             '<stop stop-color="#25352D" stop-opacity=".16"/><stop offset="1" stop-color="#25352D" stop-opacity="0"/>'
             '</radialGradient></defs>']
    positions = {'topleft': (0, 0, 0), 'topright': (r+c, 0, 90),
                 'bottomright': (r+c, r+c, 180), 'bottomleft': (0, r+c, 270)}
    for prefix, oy in (("", 0), ("mask-", 40)):
        fill = '#FFFFFF' if not prefix else '#000000'
        border = '#C5D2C8' if not prefix else '#000000'
        parts.append(f'<rect id="{prefix}center" x="{r}" y="{oy+r}" width="{c}" height="{c}" fill="{fill}"/>')
        for name, (x, y, rotation) in positions.items():
            parts.append(f'<g id="{prefix}{name}" transform="translate({x},{oy+y}) rotate({rotation},{r/2},{r/2})">'
                         f'<path fill="{border}" d="M0 {r}A{r} {r} 0 0 1 {r} 0V{r}Z"/>'
                         f'<path fill="{fill}" d="M1 {r}A{r-1} {r-1} 0 0 1 {r} 1V{r}Z"/></g>')
        # Rotate a top edge about its centre, placing each in a separate cell.
        for name, x, y, w, h, bx, by, bw, bh in (
            ('top', r, 0, c, r, r, 0, c, 1),
            ('bottom', r, r+c, c, r, r, 2*r+c-1, c, 1),
            ('left', 0, r, r, c, 0, r, 1, c),
            ('right', r+c, r, r, c, 2*r+c-1, r, 1, c),
        ):
            parts.append(f'<g id="{prefix}{name}"><rect x="{x}" y="{oy+y}" width="{w}" height="{h}" fill="{fill}"/>'
                         f'<rect x="{bx}" y="{oy+by}" width="{bw}" height="{bh}" fill="{border}"/></g>')
    for name, x, y, angle in (('topleft', 0, 90, 0), ('topright', s+c, 90, 90),
                              ('bottomright', s+c, 90+s+c, 180), ('bottomleft', 0, 90+s+c, 270)):
        parts.append(f'<rect id="shadow-{name}" x="0" y="0" width="{s}" height="{s}" fill="url(#corner)" '
                     f'transform="translate({x},{y}) rotate({angle},{s/2},{s/2})"/>')
    for name, transform in (
        ('top', f'translate({s},90)'),
        ('bottom', f'translate({s+c},{90+2*s+c}) rotate(180)'),
        ('left', f'translate(0,{90+s+c}) rotate(-90)'),
        ('right', f'translate({2*s+c},{90+s}) rotate(90)'),
    ):
        parts.append(f'<rect id="shadow-{name}" width="{c}" height="{s}" fill="url(#fade)" transform="{transform}"/>')
    for prefix, amount in (('hint-', margin), ('shadow-hint-', s)):
        for i, side in enumerate(('top', 'bottom', 'left', 'right')):
            parts.append(f'<rect id="{prefix}{side}-margin" x="{100+i*20}" y="180" width="{amount}" height="{amount}" fill="#FF00FF"/>')
    parts.append('</svg>\n')
    return '\n'.join(parts)


# Six-unit glyphs. No tiny interior details at 16px; all visible strokes >=1px.
GLYPHS = {
    'documents': '<path d="M1 .5h3l1 1V5.5H1zM2 3h2M2 4.5h2"/>',
    'download': '<path d="M3 .5v4M1.5 3 3 4.5 4.5 3M.5 5.5h5"/>',
    'home': '<path d="M.5 2.5 3 .5l2.5 2M1.5 2v3.5h3V2"/>',
    'favorites': '<path d="m3 .5 .8 1.6 1.7.3-1.3 1.3.3 1.8L3 4.6l-1.5.9.3-1.8L.5 2.4l1.7-.3z"/>',
    'desktop': '<path d="M.5 .5h5v3.5h-5zM3 4v1.5M1.5 5.5h3"/>',
    'pictures': '<path d="M.5 .5h5v5h-5zM.5 4.5l2-2 3 3"/><circle cx="4" cy="2" r=".25"/>',
    'music': '<path d="M2 4.5v-3l3-1V4"/><path d="M.5 4.5H2M3.5 4H5"/>',
    'videos': '<path d="m1.5 .5 4 2.5-4 2.5z"/>',
    'code': '<path d="m2 1.5-1.5 1.5L2 4.5m2-3 1.5 1.5L4 4.5"/>',
    'locked': '<path d="M1 2.5h4v3H1zM2 2.5v-1a1 1 0 0 1 2 0v1"/>',
    'network': '<path d="M2 .5h2v2H2zM3 2.5v1.5M.5 5.5V4h5v1.5"/>',
    'cloud': '<path d="M1.5 5a1.5 1.5 0 0 1-.4-3A2 2 0 0 1 5 2.5 1.3 1.3 0 0 1 4.5 5z"/>',
    'publicshare': '<circle cx="1" cy="3" r=".5"/><circle cx="5" cy="1" r=".5"/><circle cx="5" cy="5" r=".5"/><path d="m1.5 2.75 3-1.5m-3 2 3 1.5"/>',
    'templates': '<path d="M1 .5h4v5H1zM2.5 2h1M2.5 4h1"/>',
    'games': '<path d="M1 1.5h4l.5 3-1-.5h-3l-1 .5zM1.5 2.5h1m-.5-.5v1M4 2.5h.5"/>',
    'recent': '<circle cx="3" cy="3" r="2.5"/><path d="M3 1.5v1.5h1.5"/>',
    'activities': '<path d="M.5 3h1l1-2 1 4 1-2h1"/>',
}
ALIASES = {'downloads': 'download', 'image': 'pictures', 'sound': 'music', 'video': 'videos',
           'development': 'code', 'html': 'code', 'remote': 'network'}


def folder(size, kind):
    # Insets, tab and body coordinates deliberately snap to each native grid.
    x, y, top, bottom, radius, glyph_size = {
        16: (1, 3, 5, 14, 1, 6),
        22: (2, 4, 7, 19, 1, 8),
        32: (3, 6, 10, 28, 2, 12),
        64: (6, 11, 20, 55, 4, 24),
    }[size]
    right, tab = size-x, round(size*.41)
    front = f'M{x} {top+radius}Q{x} {top} {x+radius} {top}H{right-radius}Q{right} {top} {right} {top+radius}V{bottom-radius}Q{right} {bottom} {right-radius} {bottom}H{x+radius}Q{x} {bottom} {x} {bottom-radius}Z'
    if kind == 'open':
        front = f'M{x+3} {top+2}H{right}L{right-2} {bottom}H{x}Z'
    svg = [HEADER, f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">',
           f'<path fill="#487D66" d="M{x} {y+radius}Q{x} {y} {x+radius} {y}H{tab}L{tab+top-y} {top}H{right}V{bottom-radius}H{x}Z"/>',
           f'<path fill="#2E6B57" d="{front}"/>',
           f'<path stroke="#215342" stroke-width="1" d="M{x+radius} {bottom-.5}H{right-radius}"/>']
    kind = ALIASES.get(kind, kind)
    if kind in GLYPHS:
        scale = glyph_size / 6
        gx, gy = (size-glyph_size)/2, top+(bottom-top-glyph_size)/2
        weight = {16: 1, 22: 1.15, 32: 1.5, 64: 2.5}[size] / scale
        svg.append(f'<g transform="translate({gx},{gy}) scale({scale})" fill="none" stroke="#F4F7F2" stroke-width="{weight:.6f}" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[kind]}</g>')
    return '\n'.join(svg + ['</svg>\n'])


def main():
    for name, r, margin, shadow in (('widgets/panel-background', 6, 6, 12),
                                   ('dialogs/background', 8, 8, 16),
                                   ('widgets/background', 6, 8, 12),
                                   ('widgets/tooltip', 6, 6, 12)):
        path = STYLE / (name + '.svg')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(surface(r, margin, shadow))
    names = sorted(p.name for p in (ICONS / 'places/scalable').glob('*.svg'))
    for size, directory in ((16, '16'), (22, '22'), (32, '32'), (64, 'scalable')):
        target = ICONS / 'places' / directory
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            kind = name.removesuffix('.svg').removeprefix('folder-').removeprefix('user-')
            (target / name).write_text(folder(size, kind))


if __name__ == '__main__':
    main()
