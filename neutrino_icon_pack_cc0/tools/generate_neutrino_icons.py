#!/usr/bin/env python3
"""
Generate the Neutrino CC0-style icon pack.

This script creates original SVG geometry and themed PNG exports. No external icon
artwork is imported. Dependencies for regeneration: Python 3, cairosvg, pillow.
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cairosvg
from PIL import Image, ImageDraw

ROOT = Path('/mnt/data/neutrino_icon_pack_cc0')
ZIP_PATH = Path('/mnt/data/neutrino_icon_pack_cc0.zip')
TGZ_PATH = Path('/mnt/data/neutrino_icon_pack_cc0.tar.gz')
CANVAS = 128
SIZES = [16, 24, 32, 48, 64, 128]

THEMES: Dict[str, Dict[str, str]] = {
    'classic_gray': {
        'primary': '#2B2F36', 'secondary': '#667085', 'accent': '#2563EB',
        'overlay': '#FFFFFF', 'surface': '#FFFFFF', 'danger': '#DC2626',
        'warning': '#D97706', 'success': '#16A34A'
    },
    'neutrino_blue': {
        'primary': '#0F172A', 'secondary': '#1D4ED8', 'accent': '#3B82F6',
        'overlay': '#FFFFFF', 'surface': '#EEF6FF', 'danger': '#EF4444',
        'warning': '#F59E0B', 'success': '#22C55E'
    },
    'graphite_dark_ui': {
        'primary': '#E5E7EB', 'secondary': '#9CA3AF', 'accent': '#F59E0B',
        'overlay': '#111827', 'surface': '#111827', 'danger': '#FB7185',
        'warning': '#FBBF24', 'success': '#86EFAC'
    },
    'forest_green': {
        'primary': '#143321', 'secondary': '#166534', 'accent': '#22C55E',
        'overlay': '#FFFFFF', 'surface': '#ECFDF5', 'danger': '#B91C1C',
        'warning': '#B45309', 'success': '#16A34A'
    },
    'royal_purple': {
        'primary': '#24123A', 'secondary': '#6D28D9', 'accent': '#A855F7',
        'overlay': '#FFFFFF', 'surface': '#F5F3FF', 'danger': '#E11D48',
        'warning': '#D97706', 'success': '#059669'
    },
}

@dataclass(frozen=True)
class IconEntry:
    name: str
    category: str
    base: str
    overlay: Optional[str] = None
    tags: Tuple[str, ...] = ()


def safe(s: str) -> str:
    return s.replace(' ', '_').lower()

class Svg:
    def __init__(self, theme: Optional[Dict[str, str]], title: str, master: bool = False):
        self.theme = theme or THEMES['classic_gray']
        self.title = title
        self.master = master
        self.parts: List[str] = []

    def color(self, key: str) -> str:
        if key == 'none':
            return 'none'
        if key.startswith('#'):
            return key
        if self.master:
            return f'var(--ni-{key})'
        return self.theme.get(key, key)

    def add(self, tag: str, **attrs: object) -> None:
        items = []
        for k, v in attrs.items():
            if v is None:
                continue
            k = k.replace('_', '-')
            if isinstance(v, float):
                v = round(v, 3)
            items.append(f'{k}="{html.escape(str(v), quote=True)}"')
        self.parts.append(f'<{tag} ' + ' '.join(items) + '/>')

    def path(self, d: str, stroke: str = 'primary', fill: str = 'none', sw: float = 8,
             opacity: Optional[float] = None, fill_opacity: Optional[float] = None,
             cap: str = 'round', join: str = 'round') -> None:
        self.add('path', d=d, stroke=self.color(stroke), fill=self.color(fill), stroke_width=sw,
                 stroke_linecap=cap, stroke_linejoin=join, opacity=opacity, fill_opacity=fill_opacity)

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str = 'primary', sw: float = 8,
             cap: str = 'round', opacity: Optional[float] = None) -> None:
        self.add('line', x1=x1, y1=y1, x2=x2, y2=y2, stroke=self.color(stroke), stroke_width=sw,
                 stroke_linecap=cap, opacity=opacity)

    def rect(self, x: float, y: float, w: float, h: float, rx: float = 0, ry: Optional[float] = None,
             stroke: str = 'primary', fill: str = 'none', sw: float = 8,
             opacity: Optional[float] = None, fill_opacity: Optional[float] = None) -> None:
        self.add('rect', x=x, y=y, width=w, height=h, rx=rx, ry=ry if ry is not None else rx,
                 stroke=self.color(stroke), fill=self.color(fill), stroke_width=sw,
                 opacity=opacity, fill_opacity=fill_opacity)

    def circle(self, cx: float, cy: float, r: float, stroke: str = 'primary', fill: str = 'none', sw: float = 8,
               opacity: Optional[float] = None, fill_opacity: Optional[float] = None) -> None:
        self.add('circle', cx=cx, cy=cy, r=r, stroke=self.color(stroke), fill=self.color(fill),
                 stroke_width=sw, opacity=opacity, fill_opacity=fill_opacity)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, stroke: str = 'primary', fill: str = 'none', sw: float = 8,
                opacity: Optional[float] = None, fill_opacity: Optional[float] = None) -> None:
        self.add('ellipse', cx=cx, cy=cy, rx=rx, ry=ry, stroke=self.color(stroke), fill=self.color(fill),
                 stroke_width=sw, opacity=opacity, fill_opacity=fill_opacity)

    def polyline(self, pts: Iterable[Tuple[float, float]], stroke: str = 'primary', fill: str = 'none', sw: float = 8,
                 opacity: Optional[float] = None) -> None:
        p = ' '.join(f'{x},{y}' for x, y in pts)
        self.add('polyline', points=p, stroke=self.color(stroke), fill=self.color(fill), stroke_width=sw,
                 stroke_linecap='round', stroke_linejoin='round', opacity=opacity)

    def polygon(self, pts: Iterable[Tuple[float, float]], stroke: str = 'primary', fill: str = 'none', sw: float = 8,
                opacity: Optional[float] = None, fill_opacity: Optional[float] = None) -> None:
        p = ' '.join(f'{x},{y}' for x, y in pts)
        self.add('polygon', points=p, stroke=self.color(stroke), fill=self.color(fill), stroke_width=sw,
                 stroke_linecap='round', stroke_linejoin='round', opacity=opacity, fill_opacity=fill_opacity)

    def xml(self) -> str:
        style = ''
        if self.master:
            style = ('<style>:root{--ni-primary:#2B2F36;--ni-secondary:#667085;'
                     '--ni-accent:#2563EB;--ni-overlay:#FFFFFF;--ni-surface:#FFFFFF;'
                     '--ni-danger:#DC2626;--ni-warning:#D97706;--ni-success:#16A34A;}</style>')
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}" role="img" aria-label="{html.escape(self.title)}">'
                f'<title>{html.escape(self.title)}</title>{style}' + ''.join(self.parts) + '</svg>\n')


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5) -> List[Tuple[float, float]]:
    pts = []
    for i in range(count * 2):
        a = -math.pi / 2 + i * math.pi / count
        r = outer if i % 2 == 0 else inner
        pts.append((round(cx + math.cos(a) * r, 3), round(cy + math.sin(a) * r, 3)))
    return pts

# ---------- Base shapes ----------

def draw_file(s: Svg) -> None:
    s.path('M32 14H76L100 38V112H32Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M76 14V38H100', stroke='secondary', sw=7)
    s.line(46, 60, 82, 60, 'secondary', 6)
    s.line(46, 78, 78, 78, 'secondary', 6)


def draw_file_stack(s: Svg) -> None:
    s.path('M26 28H70L92 50V114H26Z', stroke='secondary', fill='surface', fill_opacity=0.04, sw=6)
    s.path('M38 14H82L104 36V100H38Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M82 14V36H104', stroke='secondary', sw=7)


def draw_folder(s: Svg) -> None:
    s.path('M14 38Q14 30 22 30H48L58 42H106Q114 42 114 50V100Q114 108 106 108H22Q14 108 14 100Z', stroke='primary', fill='surface', fill_opacity=0.08)
    s.line(20, 54, 108, 54, 'secondary', 6)


def draw_folder_open(s: Svg) -> None:
    s.path('M14 42Q14 34 22 34H48L58 46H110Q116 46 116 54', stroke='secondary', fill='none', sw=7)
    s.path('M18 56H112L100 108H20Z', stroke='primary', fill='surface', fill_opacity=0.08)


def draw_disk(s: Svg) -> None:
    s.rect(20, 16, 88, 96, rx=10, stroke='primary', fill='surface', fill_opacity=0.07)
    s.rect(36, 16, 48, 30, rx=3, stroke='secondary', fill='none', sw=6)
    s.rect(38, 72, 52, 32, rx=5, stroke='secondary', fill='none', sw=6)
    s.line(72, 22, 72, 40, 'secondary', 5)


def draw_clipboard(s: Svg) -> None:
    s.rect(28, 24, 72, 88, rx=9, stroke='primary', fill='surface', fill_opacity=0.06)
    s.rect(46, 14, 36, 20, rx=7, stroke='secondary', fill='surface', fill_opacity=0.06, sw=6)
    for y, w in [(54, 42), (72, 48), (90, 34)]:
        s.line(42, y, 42 + w, y, 'secondary', 6)


def draw_trash(s: Svg) -> None:
    s.line(36, 36, 92, 36, 'primary', 8)
    s.line(50, 22, 78, 22, 'secondary', 7)
    s.path('M42 42L48 110H80L86 42', stroke='primary', sw=8)
    s.line(56, 54, 58, 98, 'secondary', 5)
    s.line(72, 54, 70, 98, 'secondary', 5)


def draw_pencil(s: Svg) -> None:
    s.path('M28 92L34 112L54 106L102 58Q108 52 102 46L86 30Q80 24 74 30Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(72, 36, 96, 60, 'secondary', 7)
    s.line(34, 112, 46, 100, 'secondary', 6)


def draw_scissors(s: Svg) -> None:
    s.circle(34, 38, 14, 'primary', 'none', 7)
    s.circle(34, 90, 14, 'primary', 'none', 7)
    s.line(46, 48, 100, 100, 'primary', 7)
    s.line(46, 80, 100, 28, 'primary', 7)
    s.circle(64, 64, 4, 'secondary', 'secondary', 2)


def draw_copy(s: Svg) -> None:
    s.rect(30, 30, 58, 70, rx=7, stroke='secondary', fill='surface', fill_opacity=0.04, sw=7)
    s.rect(46, 18, 58, 70, rx=7, stroke='primary', fill='surface', fill_opacity=0.06, sw=7)


def draw_link(s: Svg) -> None:
    s.path('M52 44L42 44Q24 44 24 64Q24 84 42 84H58', stroke='primary', sw=9)
    s.path('M76 44H86Q104 44 104 64Q104 84 86 84H70', stroke='primary', sw=9)
    s.line(48, 64, 80, 64, 'secondary', 8)


def draw_unlink(s: Svg) -> None:
    draw_link(s)
    s.line(36, 98, 92, 30, 'danger', 8)


def draw_search(s: Svg) -> None:
    s.circle(54, 54, 30, 'primary', 'none', 8)
    s.line(77, 77, 106, 106, 'primary', 9)


def draw_filter(s: Svg) -> None:
    s.path('M20 26H108L76 64V102L52 112V64Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_sort(s: Svg) -> None:
    s.line(42, 28, 42, 100, 'primary', 8)
    s.polyline([(28, 44), (42, 28), (56, 44)], 'primary', 'none', 8)
    s.line(86, 100, 86, 28, 'secondary', 8)
    s.polyline([(72, 84), (86, 100), (100, 84)], 'secondary', 'none', 8)


def draw_eye(s: Svg) -> None:
    s.path('M12 64Q36 28 64 28Q92 28 116 64Q92 100 64 100Q36 100 12 64Z', stroke='primary', fill='surface', fill_opacity=0.04)
    s.circle(64, 64, 16, 'secondary', 'none', 7)


def draw_slash(s: Svg) -> None:
    s.line(28, 106, 100, 22, 'danger', 9)


def draw_lock(s: Svg) -> None:
    s.rect(30, 58, 68, 52, rx=9, stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M44 58V44Q44 22 64 22Q84 22 84 44V58', stroke='secondary', sw=8)
    s.line(64, 78, 64, 92, 'secondary', 7)


def draw_unlock(s: Svg) -> None:
    s.rect(30, 58, 68, 52, rx=9, stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M44 58V44Q44 24 64 24Q82 24 86 42', stroke='secondary', sw=8)
    s.line(64, 78, 64, 92, 'secondary', 7)


def draw_key(s: Svg) -> None:
    s.circle(42, 52, 20, 'primary', 'none', 8)
    s.line(58, 66, 104, 104, 'primary', 8)
    s.line(88, 90, 100, 78, 'secondary', 6)
    s.line(98, 100, 110, 88, 'secondary', 6)


def draw_shield(s: Svg) -> None:
    s.path('M64 14L104 30V60Q104 92 64 114Q24 92 24 60V30Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M46 64L58 76L84 48', stroke='secondary', sw=8)


def draw_user(s: Svg) -> None:
    s.circle(64, 42, 20, 'primary', 'none', 8)
    s.path('M26 108Q34 78 64 78Q94 78 102 108', stroke='primary', sw=8)


def draw_group(s: Svg) -> None:
    s.circle(48, 44, 16, 'secondary', 'none', 7)
    s.circle(82, 42, 18, 'primary', 'none', 8)
    s.path('M20 106Q26 80 50 80', stroke='secondary', sw=7)
    s.path('M48 108Q56 78 82 78Q108 78 116 108', stroke='primary', sw=8)


def draw_calendar(s: Svg) -> None:
    s.rect(20, 26, 88, 82, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(20, 50, 108, 50, 'secondary', 7)
    s.line(42, 16, 42, 34, 'primary', 8)
    s.line(86, 16, 86, 34, 'primary', 8)
    for x in [42, 64, 86]:
        for y in [68, 88]:
            s.circle(x, y, 3.5, 'secondary', 'secondary', 1)


def draw_clock(s: Svg) -> None:
    s.circle(64, 64, 46, 'primary', 'none', 8)
    s.line(64, 64, 64, 36, 'secondary', 7)
    s.line(64, 64, 86, 76, 'secondary', 7)


def draw_cloud(s: Svg) -> None:
    s.path('M34 94Q18 94 18 78Q18 62 34 60Q40 38 64 38Q86 38 94 58Q112 60 112 76Q112 94 94 94Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_database(s: Svg) -> None:
    s.ellipse(64, 28, 38, 14, 'primary', 'surface', 8, fill_opacity=0.06)
    s.path('M26 28V96Q26 110 64 110Q102 110 102 96V28', stroke='primary', sw=8)
    s.ellipse(64, 62, 38, 14, 'secondary', 'none', 6)
    s.ellipse(64, 94, 38, 14, 'secondary', 'none', 6)


def draw_server(s: Svg) -> None:
    s.rect(22, 20, 84, 34, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.rect(22, 74, 84, 34, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(40, 37, 4, 'secondary', 'secondary', 1)
    s.circle(40, 91, 4, 'secondary', 'secondary', 1)
    s.line(60, 37, 92, 37, 'secondary', 5)
    s.line(60, 91, 92, 91, 'secondary', 5)


def draw_network(s: Svg) -> None:
    pts = [(64, 26), (28, 86), (100, 86)]
    s.line(64, 26, 28, 86, 'secondary', 6)
    s.line(64, 26, 100, 86, 'secondary', 6)
    s.line(28, 86, 100, 86, 'secondary', 6)
    for x, y in pts:
        s.circle(x, y, 13, 'primary', 'surface', 7, fill_opacity=0.06)


def draw_wifi(s: Svg) -> None:
    s.path('M22 50Q64 18 106 50', stroke='primary', sw=8)
    s.path('M40 70Q64 50 88 70', stroke='primary', sw=8)
    s.path('M55 90Q64 82 73 90', stroke='secondary', sw=8)
    s.circle(64, 104, 4, 'secondary', 'secondary', 2)


def draw_bluetooth(s: Svg) -> None:
    s.path('M54 18L86 48L62 64L86 82L54 112V18Z', stroke='primary', fill='surface', fill_opacity=0.04)
    s.line(28, 42, 62, 64, 'secondary', 7)
    s.line(28, 86, 62, 64, 'secondary', 7)


def draw_globe(s: Svg) -> None:
    s.circle(64, 64, 48, 'primary', 'none', 8)
    s.path('M16 64H112', stroke='secondary', sw=6)
    s.path('M64 16Q46 40 46 64Q46 88 64 112', stroke='secondary', sw=6)
    s.path('M64 16Q82 40 82 64Q82 88 64 112', stroke='secondary', sw=6)


def draw_mail(s: Svg) -> None:
    s.rect(18, 34, 92, 64, rx=9, stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M22 42L64 72L106 42', stroke='secondary', sw=7)


def draw_message(s: Svg) -> None:
    s.path('M22 30H106V84Q106 94 96 94H58L30 112V94H22Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(42, 52, 86, 52, 'secondary', 6)
    s.line(42, 70, 76, 70, 'secondary', 6)


def draw_bell(s: Svg) -> None:
    s.path('M34 84V58Q34 32 64 32Q94 32 94 58V84L106 100H22Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(54, 108, 74, 108, 'secondary', 7)
    s.line(64, 22, 64, 28, 'secondary', 7)


def draw_tag(s: Svg) -> None:
    s.path('M20 58L58 20H102V64L64 108Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(82, 42, 6, 'secondary', 'none', 5)


def draw_bookmark(s: Svg) -> None:
    s.path('M38 18H90V112L64 94L38 112Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_flag(s: Svg) -> None:
    s.line(30, 18, 30, 112, 'primary', 8)
    s.path('M34 22H94L84 48L96 74H34Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_home(s: Svg) -> None:
    s.path('M16 62L64 22L112 62', stroke='primary', sw=8)
    s.path('M30 58V108H54V78H74V108H98V58', stroke='primary', fill='surface', fill_opacity=0.04, sw=8)


def draw_window(s: Svg) -> None:
    s.rect(16, 20, 96, 88, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(16, 44, 112, 44, 'secondary', 6)
    for x in [34, 50, 66]:
        s.circle(x, 32, 3.2, 'secondary', 'secondary', 1)


def draw_browser(s: Svg) -> None:
    draw_window(s)
    s.circle(64, 76, 22, 'secondary', 'none', 6)
    s.path('M42 76H86', stroke='secondary', sw=5)


def draw_terminal(s: Svg) -> None:
    s.rect(16, 20, 96, 88, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.polyline([(34, 54), (52, 70), (34, 86)], 'secondary', 'none', 7)
    s.line(60, 88, 88, 88, 'secondary', 7)


def draw_code(s: Svg) -> None:
    s.polyline([(50, 34), (22, 64), (50, 94)], 'primary', 'none', 8)
    s.polyline([(78, 34), (106, 64), (78, 94)], 'primary', 'none', 8)
    s.line(70, 24, 58, 104, 'secondary', 7)


def draw_grid(s: Svg) -> None:
    for x in [24, 54, 84]:
        for y in [24, 54, 84]:
            s.rect(x, y, 20, 20, rx=4, stroke='primary', fill='surface', sw=6, fill_opacity=0.04)


def draw_list(s: Svg) -> None:
    for y in [34, 64, 94]:
        s.circle(30, y, 4, 'primary', 'primary', 1)
        s.line(46, y, 100, y, 'primary', 7)


def draw_table(s: Svg) -> None:
    s.rect(18, 22, 92, 84, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(18, 50, 110, 50, 'secondary', 6)
    s.line(18, 78, 110, 78, 'secondary', 6)
    s.line(50, 22, 50, 106, 'secondary', 6)
    s.line(80, 22, 80, 106, 'secondary', 6)


def draw_image(s: Svg) -> None:
    s.rect(18, 24, 92, 80, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(44, 48, 8, 'secondary', 'none', 5)
    s.path('M28 94L54 68L72 84L86 70L104 94', stroke='secondary', sw=7)


def draw_video(s: Svg) -> None:
    s.rect(20, 34, 64, 60, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.polygon([(84, 54), (108, 40), (108, 88), (84, 74)], 'primary', 'surface', 7, fill_opacity=0.06)


def draw_audio(s: Svg) -> None:
    s.path('M42 74V34L88 24V80', stroke='primary', sw=8)
    s.circle(34, 84, 14, 'primary', 'surface', 7, fill_opacity=0.06)
    s.circle(80, 90, 14, 'primary', 'surface', 7, fill_opacity=0.06)


def draw_play(s: Svg) -> None:
    s.polygon([(42, 28), (100, 64), (42, 100)], 'primary', 'surface', 8, fill_opacity=0.06)


def draw_pause(s: Svg) -> None:
    s.rect(38, 28, 16, 72, rx=4, stroke='primary', fill='primary', sw=4)
    s.rect(74, 28, 16, 72, rx=4, stroke='primary', fill='primary', sw=4)


def draw_stop(s: Svg) -> None:
    s.rect(34, 34, 60, 60, rx=8, stroke='primary', fill='surface', sw=8, fill_opacity=0.06)


def draw_record(s: Svg) -> None:
    s.circle(64, 64, 34, 'danger', 'danger', 4, fill_opacity=0.8)


def draw_speaker(s: Svg) -> None:
    s.path('M20 54H42L70 30V98L42 74H20Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M82 48Q94 64 82 80', stroke='secondary', sw=7)
    s.path('M94 36Q114 64 94 92', stroke='secondary', sw=7)


def draw_microphone(s: Svg) -> None:
    s.rect(46, 18, 36, 62, rx=18, stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M28 62Q28 98 64 98Q100 98 100 62', stroke='secondary', sw=8)
    s.line(64, 98, 64, 114, 'primary', 8)
    s.line(46, 114, 82, 114, 'primary', 8)


def draw_camera(s: Svg) -> None:
    s.rect(18, 38, 92, 60, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M42 38L50 26H78L86 38', stroke='secondary', sw=7)
    s.circle(64, 68, 18, 'secondary', 'none', 7)


def draw_printer(s: Svg) -> None:
    s.rect(28, 18, 72, 34, rx=4, stroke='secondary', fill='surface', sw=6, fill_opacity=0.06)
    s.rect(20, 48, 88, 42, rx=9, stroke='primary', fill='surface', sw=8, fill_opacity=0.06)
    s.rect(34, 78, 60, 34, rx=4, stroke='primary', fill='surface', sw=7, fill_opacity=0.06)
    s.circle(92, 66, 3.5, 'secondary', 'secondary', 1)


def draw_monitor(s: Svg) -> None:
    s.rect(18, 24, 92, 64, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(64, 88, 64, 106, 'primary', 8)
    s.line(42, 108, 86, 108, 'primary', 8)


def draw_phone(s: Svg) -> None:
    s.rect(40, 16, 48, 96, rx=12, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(56, 30, 72, 30, 'secondary', 5)
    s.circle(64, 98, 3, 'secondary', 'secondary', 1)


def draw_tablet(s: Svg) -> None:
    s.rect(30, 16, 68, 96, rx=12, stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(64, 100, 3, 'secondary', 'secondary', 1)


def draw_keyboard(s: Svg) -> None:
    s.rect(14, 40, 100, 58, rx=10, stroke='primary', fill='surface', fill_opacity=0.06)
    for y in [58, 76]:
        for x in [30, 46, 62, 78, 94]:
            s.rect(x - 4, y - 4, 8, 8, rx=2, stroke='secondary', fill='secondary', sw=1)
    s.line(40, 90, 88, 90, 'secondary', 5)


def draw_mouse(s: Svg) -> None:
    s.rect(42, 16, 44, 96, rx=22, stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(64, 18, 64, 50, 'secondary', 6)
    s.line(42, 54, 86, 54, 'secondary', 6)


def draw_cpu(s: Svg) -> None:
    s.rect(34, 34, 60, 60, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.rect(50, 50, 28, 28, rx=4, stroke='secondary', fill='none', sw=6)
    for x in [28, 100]:
        for y in [44, 64, 84]:
            s.line(x, y, x + (6 if x == 28 else -6), y, 'primary', 5)
    for y in [28, 100]:
        for x in [44, 64, 84]:
            s.line(x, y, x, y + (6 if y == 28 else -6), 'primary', 5)


def draw_memory(s: Svg) -> None:
    s.rect(22, 40, 84, 48, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    for x in [38, 56, 74, 92]:
        s.rect(x - 5, 54, 10, 20, rx=2, stroke='secondary', fill='none', sw=4)
    for x in [34, 50, 66, 82, 98]:
        s.line(x, 88, x, 104, 'primary', 5)


def draw_harddrive(s: Svg) -> None:
    s.path('M34 20H94L110 74V104Q110 112 102 112H26Q18 112 18 104V74Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(18, 74, 110, 74, 'secondary', 6)
    s.circle(38, 94, 4, 'secondary', 'secondary', 1)
    s.circle(54, 94, 4, 'secondary', 'secondary', 1)


def draw_usb(s: Svg) -> None:
    s.path('M64 18V86', stroke='primary', sw=8)
    s.polyline([(48, 34), (64, 18), (80, 34)], 'primary', 'none', 8)
    s.path('M64 52H36V70', stroke='secondary', sw=6)
    s.path('M64 64H92V46', stroke='secondary', sw=6)
    s.circle(36, 78, 8, 'secondary', 'none', 5)
    s.rect(84, 32, 16, 16, rx=2, stroke='secondary', fill='none', sw=5)
    s.circle(64, 100, 10, 'primary', 'none', 7)


def draw_battery(s: Svg) -> None:
    s.rect(18, 44, 84, 40, rx=8, stroke='primary', fill='surface', fill_opacity=0.06)
    s.rect(104, 56, 8, 16, rx=2, stroke='primary', fill='primary', sw=2)
    s.rect(30, 54, 48, 20, rx=3, stroke='secondary', fill='secondary', sw=2, fill_opacity=0.3)


def draw_chart_bar(s: Svg) -> None:
    s.line(20, 106, 108, 106, 'primary', 7)
    for x, h in [(34, 34), (62, 58), (90, 78)]:
        s.rect(x - 8, 106 - h, 16, h, rx=4, stroke='primary', fill='surface', sw=6, fill_opacity=0.06)


def draw_chart_line(s: Svg) -> None:
    s.line(20, 106, 108, 106, 'primary', 7)
    s.line(22, 108, 22, 22, 'primary', 7)
    s.polyline([(30, 88), (50, 68), (68, 76), (92, 42), (108, 52)], 'secondary', 'none', 8)


def draw_pie(s: Svg) -> None:
    s.path('M64 18A46 46 0 1 1 30 94L64 64Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M64 18A46 46 0 0 1 110 64H64Z', stroke='secondary', fill='none', sw=7)


def draw_gauge(s: Svg) -> None:
    s.path('M22 92A48 48 0 0 1 106 92', stroke='primary', sw=8)
    s.line(64, 86, 92, 50, 'secondary', 7)
    s.circle(64, 86, 6, 'secondary', 'secondary', 2)
    s.line(28, 92, 40, 92, 'secondary', 5)
    s.line(100, 92, 88, 92, 'secondary', 5)


def draw_gear(s: Svg) -> None:
    for a in range(0, 360, 45):
        r1, r2 = 38, 50
        x1 = 64 + math.cos(math.radians(a)) * r1
        y1 = 64 + math.sin(math.radians(a)) * r1
        x2 = 64 + math.cos(math.radians(a)) * r2
        y2 = 64 + math.sin(math.radians(a)) * r2
        s.line(x1, y1, x2, y2, 'primary', 8)
    s.circle(64, 64, 34, 'primary', 'surface', 8, fill_opacity=0.04)
    s.circle(64, 64, 12, 'secondary', 'none', 7)


def draw_wrench(s: Svg) -> None:
    s.path('M82 20Q98 26 102 42L84 60L68 44L86 26Q84 22 82 20Z', stroke='primary', fill='surface', fill_opacity=0.04)
    s.line(72, 54, 26, 100, 'primary', 10)
    s.circle(24, 102, 8, 'secondary', 'none', 5)


def draw_hammer(s: Svg) -> None:
    s.path('M42 28L84 16L102 34L90 46L78 34L56 48Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(70, 42, 30, 104, 'primary', 10)


def draw_bug(s: Svg) -> None:
    s.ellipse(64, 68, 28, 36, 'primary', 'surface', 8, fill_opacity=0.06)
    s.circle(64, 28, 14, 'primary', 'none', 7)
    s.line(50, 44, 78, 44, 'secondary', 6)
    for y in [58, 76, 94]:
        s.line(36, y, 20, y - 10, 'secondary', 5)
        s.line(92, y, 108, y - 10, 'secondary', 5)


def draw_box(s: Svg) -> None:
    s.path('M22 44L64 20L106 44V94L64 118L22 94Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M22 44L64 68L106 44', stroke='secondary', sw=6)
    s.path('M64 68V118', stroke='secondary', sw=6)


def draw_package(s: Svg) -> None:
    draw_box(s)
    s.path('M44 32L86 56', stroke='secondary', sw=5)


def draw_rocket(s: Svg) -> None:
    s.path('M48 84L44 104L64 92L84 104L80 84Q104 62 98 24Q60 18 38 46Q24 66 48 84Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(72, 48, 8, 'secondary', 'none', 5)
    s.path('M44 104L32 112L36 96', stroke='warning', sw=6)


def draw_location(s: Svg) -> None:
    s.path('M64 114Q28 74 28 48Q28 20 64 20Q100 20 100 48Q100 74 64 114Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(64, 50, 14, 'secondary', 'none', 7)


def draw_map(s: Svg) -> None:
    s.path('M18 34L48 22L80 34L110 22V94L80 106L48 94L18 106Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(48, 22, 48, 94, 'secondary', 6)
    s.line(80, 34, 80, 106, 'secondary', 6)


def draw_compass(s: Svg) -> None:
    s.circle(64, 64, 48, 'primary', 'none', 8)
    s.polygon([(78, 34), (64, 70), (50, 94), (64, 58)], 'secondary', 'surface', 6, fill_opacity=0.06)


def draw_book(s: Svg) -> None:
    s.path('M24 24H58Q68 24 68 34V108Q68 98 58 98H24Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M104 24H70Q60 24 60 34V108Q60 98 70 98H104Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(64, 34, 64, 108, 'secondary', 5)


def draw_brush(s: Svg) -> None:
    s.path('M78 22L106 50L64 92L48 76Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.path('M48 76Q36 80 32 94Q28 108 16 110Q42 120 58 100Q66 90 64 92', stroke='secondary', fill='surface', sw=7, fill_opacity=0.04)


def draw_palette(s: Svg) -> None:
    s.path('M64 22Q106 22 110 62Q114 98 82 98H72Q62 98 62 108Q62 116 52 116Q18 110 18 68Q18 22 64 22Z', stroke='primary', fill='surface', fill_opacity=0.06)
    for x, y in [(44, 50), (66, 42), (88, 56), (52, 78)]:
        s.circle(x, y, 5, 'secondary', 'secondary', 1)


def draw_crop(s: Svg) -> None:
    s.line(34, 14, 34, 94, 'primary', 8)
    s.line(14, 34, 94, 34, 'primary', 8)
    s.line(94, 34, 94, 114, 'secondary', 8)
    s.line(34, 94, 114, 94, 'secondary', 8)


def draw_selection(s: Svg) -> None:
    s.rect(24, 24, 80, 80, rx=4, stroke='primary', fill='none', sw=5, opacity=0.7)
    for x, y in [(24,24),(64,24),(104,24),(24,64),(104,64),(24,104),(64,104),(104,104)]:
        s.rect(x-4, y-4, 8, 8, rx=2, stroke='secondary', fill='surface', sw=3)


def draw_cursor(s: Svg) -> None:
    s.path('M30 16L96 82L66 88L52 114Z', stroke='primary', fill='surface', fill_opacity=0.08)


def draw_hand(s: Svg) -> None:
    s.path('M46 72V34Q46 26 54 26Q62 26 62 34V62V28Q62 20 70 20Q78 20 78 28V64V38Q78 30 86 30Q94 30 94 38V72Q100 62 108 68Q112 72 108 80L96 104Q90 116 72 116H56Q42 116 34 104L22 82Q18 74 26 70Q34 66 40 78Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_lightbulb(s: Svg) -> None:
    s.path('M42 58Q42 28 64 28Q86 28 86 58Q86 72 76 84V96H52V84Q42 72 42 58Z', stroke='primary', fill='surface', fill_opacity=0.06)
    s.line(52, 108, 76, 108, 'secondary', 7)
    s.line(56, 96, 72, 96, 'secondary', 5)


def draw_power(s: Svg) -> None:
    s.line(64, 20, 64, 64, 'primary', 9)
    s.path('M42 42Q22 58 24 82Q28 108 64 110Q100 108 104 82Q106 58 86 42', stroke='primary', sw=9)


def draw_sun(s: Svg) -> None:
    s.circle(64, 64, 22, 'primary', 'none', 8)
    for a in range(0, 360, 45):
        x1 = 64 + math.cos(math.radians(a)) * 36
        y1 = 64 + math.sin(math.radians(a)) * 36
        x2 = 64 + math.cos(math.radians(a)) * 50
        y2 = 64 + math.sin(math.radians(a)) * 50
        s.line(x1, y1, x2, y2, 'secondary', 7)


def draw_moon(s: Svg) -> None:
    s.path('M88 104Q54 106 34 80Q14 54 30 28Q42 48 66 58Q90 68 108 58Q108 86 88 104Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_heart(s: Svg) -> None:
    s.path('M64 108L24 68Q8 50 24 34Q42 18 64 44Q86 18 104 34Q120 50 104 68Z', stroke='primary', fill='surface', fill_opacity=0.06)


def draw_star(s: Svg) -> None:
    s.polygon(star_points(64, 64, 46, 20), 'primary', 'surface', 8, fill_opacity=0.06)


def draw_warning(s: Svg) -> None:
    s.path('M64 18L116 108H12Z', stroke='warning', fill='surface', fill_opacity=0.08, sw=8)
    s.line(64, 48, 64, 76, 'warning', 8)
    s.circle(64, 94, 4, 'warning', 'warning', 2)


def draw_info(s: Svg) -> None:
    s.circle(64, 64, 48, 'primary', 'none', 8)
    s.line(64, 58, 64, 92, 'secondary', 8)
    s.circle(64, 38, 4, 'secondary', 'secondary', 2)


def draw_help(s: Svg) -> None:
    s.circle(64, 64, 48, 'primary', 'none', 8)
    s.path('M48 48Q50 32 66 32Q82 32 84 48Q86 62 68 70V78', stroke='secondary', sw=8)
    s.circle(68, 94, 4, 'secondary', 'secondary', 2)


def draw_plus(s: Svg) -> None:
    s.line(64, 28, 64, 100, 'primary', 10)
    s.line(28, 64, 100, 64, 'primary', 10)


def draw_minus(s: Svg) -> None:
    s.line(28, 64, 100, 64, 'primary', 10)


def draw_check(s: Svg) -> None:
    s.path('M26 66L54 94L104 36', stroke='success', sw=11)


def draw_close(s: Svg) -> None:
    s.line(34, 34, 94, 94, 'danger', 10)
    s.line(94, 34, 34, 94, 'danger', 10)


def draw_arrow_dir(s: Svg, direction: str) -> None:
    if direction == 'left':
        s.line(30, 64, 100, 64, 'primary', 9)
        s.polyline([(52, 36), (24, 64), (52, 92)], 'primary', 'none', 9)
    elif direction == 'right':
        s.line(28, 64, 98, 64, 'primary', 9)
        s.polyline([(76, 36), (104, 64), (76, 92)], 'primary', 'none', 9)
    elif direction == 'up':
        s.line(64, 100, 64, 30, 'primary', 9)
        s.polyline([(36, 52), (64, 24), (92, 52)], 'primary', 'none', 9)
    else:
        s.line(64, 28, 64, 98, 'primary', 9)
        s.polyline([(36, 76), (64, 104), (92, 76)], 'primary', 'none', 9)


def draw_chevron_dir(s: Svg, direction: str) -> None:
    if direction == 'left':
        s.polyline([(78, 28), (42, 64), (78, 100)], 'primary', 'none', 10)
    elif direction == 'right':
        s.polyline([(50, 28), (86, 64), (50, 100)], 'primary', 'none', 10)
    elif direction == 'up':
        s.polyline([(28, 78), (64, 42), (100, 78)], 'primary', 'none', 10)
    else:
        s.polyline([(28, 50), (64, 86), (100, 50)], 'primary', 'none', 10)


def draw_refresh(s: Svg) -> None:
    s.path('M98 46Q84 24 56 28Q32 32 24 56', stroke='primary', sw=8)
    s.polyline([(98, 22), (98, 46), (74, 46)], 'primary', 'none', 8)
    s.path('M30 82Q44 104 72 100Q96 96 104 72', stroke='secondary', sw=8)
    s.polyline([(30, 106), (30, 82), (54, 82)], 'secondary', 'none', 8)


def draw_undo(s: Svg) -> None:
    s.path('M48 42H78Q104 42 104 68Q104 96 72 96H42', stroke='primary', sw=8)
    s.polyline([(52, 22), (28, 42), (52, 62)], 'primary', 'none', 8)


def draw_redo(s: Svg) -> None:
    s.path('M80 42H50Q24 42 24 68Q24 96 56 96H86', stroke='primary', sw=8)
    s.polyline([(76, 22), (100, 42), (76, 62)], 'primary', 'none', 8)


def draw_menu(s: Svg) -> None:
    for y in [38, 64, 90]:
        s.line(28, y, 100, y, 'primary', 9)


def draw_ellipsis_h(s: Svg) -> None:
    for x in [42, 64, 86]:
        s.circle(x, 64, 6, 'primary', 'primary', 1)


def draw_ellipsis_v(s: Svg) -> None:
    for y in [42, 64, 86]:
        s.circle(64, y, 6, 'primary', 'primary', 1)


def draw_align(s: Svg, mode: str) -> None:
    if mode == 'left':
        lines = [(28, 36, 100), (28, 58, 78), (28, 80, 100), (28, 102, 86)]
    elif mode == 'center':
        lines = [(28, 36, 100), (40, 58, 88), (28, 80, 100), (34, 102, 94)]
    elif mode == 'right':
        lines = [(28, 36, 100), (50, 58, 100), (28, 80, 100), (42, 102, 100)]
    else:
        lines = [(28, 36, 100), (28, 58, 100), (28, 80, 100), (28, 102, 100)]
    for x1, y, x2 in lines:
        s.line(x1, y, x2, y, 'primary', 7)


def draw_text_lines(s: Svg) -> None:
    for y, w in [(30, 78), (50, 68), (70, 78), (90, 58)]:
        s.line(26, y, 26 + w, y, 'primary', 7)


def draw_bold(s: Svg) -> None:
    s.path('M40 24V104H70Q92 104 92 84Q92 66 72 64Q88 60 88 44Q88 24 68 24Z', stroke='primary', fill='surface', sw=8, fill_opacity=0.05)
    s.line(40, 64, 70, 64, 'secondary', 6)


def draw_italic(s: Svg) -> None:
    s.line(54, 24, 94, 24, 'primary', 8)
    s.line(34, 104, 74, 104, 'primary', 8)
    s.line(74, 24, 54, 104, 'primary', 10)


def draw_underline(s: Svg) -> None:
    s.path('M40 28V62Q40 84 64 84Q88 84 88 62V28', stroke='primary', sw=9)
    s.line(34, 104, 94, 104, 'secondary', 8)


def draw_strikethrough(s: Svg) -> None:
    s.path('M88 36Q74 24 56 28Q38 32 38 48Q38 62 62 64Q88 66 90 84Q92 104 64 104Q44 104 32 92', stroke='primary', sw=8)
    s.line(24, 66, 104, 66, 'secondary', 8)


def draw_paragraph(s: Svg) -> None:
    s.path('M88 24H58Q34 24 34 48Q34 72 58 72H68V104', stroke='primary', sw=8)
    s.line(88, 24, 88, 104, 'primary', 8)
    s.line(68, 24, 68, 104, 'secondary', 6)


def draw_quote(s: Svg) -> None:
    s.path('M44 42Q30 52 30 72V92H52V70H42Q42 56 54 48Z', stroke='primary', fill='surface', sw=7, fill_opacity=0.05)
    s.path('M88 42Q74 52 74 72V92H96V70H86Q86 56 98 48Z', stroke='primary', fill='surface', sw=7, fill_opacity=0.05)


def draw_indent(s: Svg, decrease: bool = False) -> None:
    for y in [34, 56, 78, 100]:
        s.line(54 if y == 56 else 28, y, 100, y, 'primary', 7)
    if decrease:
        s.polyline([(46, 46), (28, 64), (46, 82)], 'secondary', 'none', 8)
    else:
        s.polyline([(28, 46), (46, 64), (28, 82)], 'secondary', 'none', 8)


def draw_supsub(s: Svg, mode: str) -> None:
    s.path('M34 42L70 90M70 42L34 90', stroke='primary', sw=8)
    if mode == 'super':
        s.rect(78, 22, 26, 26, rx=5, stroke='secondary', fill='surface', sw=5, fill_opacity=0.05)
    else:
        s.rect(78, 80, 26, 26, rx=5, stroke='secondary', fill='surface', sw=5, fill_opacity=0.05)


def draw_default(s: Svg) -> None:
    s.rect(24, 24, 80, 80, rx=18, stroke='primary', fill='surface', fill_opacity=0.06)
    s.circle(64, 64, 18, 'secondary', 'none', 7)


BASE_DRAWERS = {
    'file': draw_file, 'file_stack': draw_file_stack, 'folder': draw_folder, 'folder_open': draw_folder_open,
    'disk': draw_disk, 'clipboard': draw_clipboard, 'trash': draw_trash, 'pencil': draw_pencil,
    'scissors': draw_scissors, 'copy': draw_copy, 'link': draw_link, 'unlink': draw_unlink,
    'search': draw_search, 'filter': draw_filter, 'sort': draw_sort, 'eye': draw_eye,
    'lock': draw_lock, 'unlock': draw_unlock, 'key': draw_key, 'shield': draw_shield,
    'user': draw_user, 'group': draw_group, 'calendar': draw_calendar, 'clock': draw_clock,
    'cloud': draw_cloud, 'database': draw_database, 'server': draw_server, 'network': draw_network,
    'wifi': draw_wifi, 'bluetooth': draw_bluetooth, 'globe': draw_globe, 'mail': draw_mail,
    'message': draw_message, 'bell': draw_bell, 'tag': draw_tag, 'bookmark': draw_bookmark,
    'flag': draw_flag, 'home': draw_home, 'window': draw_window, 'browser': draw_browser,
    'terminal': draw_terminal, 'code': draw_code, 'grid': draw_grid, 'list': draw_list,
    'table': draw_table, 'image': draw_image, 'video': draw_video, 'audio': draw_audio,
    'play': draw_play, 'pause': draw_pause, 'stop': draw_stop, 'record': draw_record,
    'speaker': draw_speaker, 'microphone': draw_microphone, 'camera': draw_camera, 'printer': draw_printer,
    'monitor': draw_monitor, 'phone': draw_phone, 'tablet': draw_tablet, 'keyboard': draw_keyboard,
    'mouse': draw_mouse, 'cpu': draw_cpu, 'memory': draw_memory, 'harddrive': draw_harddrive,
    'usb': draw_usb, 'battery': draw_battery, 'chart_bar': draw_chart_bar, 'chart_line': draw_chart_line,
    'pie': draw_pie, 'gauge': draw_gauge, 'gear': draw_gear, 'wrench': draw_wrench,
    'hammer': draw_hammer, 'bug': draw_bug, 'box': draw_box, 'package': draw_package,
    'rocket': draw_rocket, 'location': draw_location, 'map': draw_map, 'compass': draw_compass,
    'book': draw_book, 'brush': draw_brush, 'palette': draw_palette, 'crop': draw_crop,
    'selection': draw_selection, 'cursor': draw_cursor, 'hand': draw_hand, 'lightbulb': draw_lightbulb,
    'power': draw_power, 'sun': draw_sun, 'moon': draw_moon, 'heart': draw_heart, 'star': draw_star,
    'warning': draw_warning, 'info': draw_info, 'help': draw_help, 'plus': draw_plus, 'minus': draw_minus,
    'check': draw_check, 'close': draw_close, 'refresh': draw_refresh, 'undo': draw_undo,
    'redo': draw_redo, 'menu': draw_menu, 'ellipsis_h': draw_ellipsis_h, 'ellipsis_v': draw_ellipsis_v,
    'text': draw_text_lines, 'bold': draw_bold, 'italic': draw_italic, 'underline': draw_underline,
    'strikethrough': draw_strikethrough, 'paragraph': draw_paragraph, 'quote': draw_quote,
}

# Dynamic direct base drawing aliases.
def draw_base(s: Svg, base: str) -> None:
    if base.startswith('arrow_'):
        draw_arrow_dir(s, base.split('_', 1)[1])
        return
    if base.startswith('chevron_'):
        draw_chevron_dir(s, base.split('_', 1)[1])
        return
    if base.startswith('align_'):
        draw_align(s, base.split('_', 1)[1])
        return
    if base == 'indent_increase':
        draw_indent(s, False)
        return
    if base == 'indent_decrease':
        draw_indent(s, True)
        return
    if base == 'superscript':
        draw_supsub(s, 'super')
        return
    if base == 'subscript':
        draw_supsub(s, 'sub')
        return
    BASE_DRAWERS.get(base, draw_default)(s)

# ---------- Overlay badges ----------

def badge_circle(s: Svg, fill: str = 'accent') -> None:
    s.circle(94, 94, 26, stroke=fill, fill=fill, sw=2, fill_opacity=0.96)


def badge_symbol(s: Svg, kind: str) -> None:
    # All symbols are inside a 52x52 bottom-right badge. Use overlay color for readability.
    fg = 'overlay'
    if kind in ('add', 'new', 'plus'):
        s.line(94, 80, 94, 108, fg, 6)
        s.line(80, 94, 108, 94, fg, 6)
    elif kind in ('remove', 'minus'):
        s.line(80, 94, 108, 94, fg, 6)
    elif kind in ('check', 'ok', 'apply'):
        s.path('M80 94L90 104L110 82', stroke=fg, sw=6)
    elif kind in ('close', 'error', 'delete', 'x'):
        s.line(82, 82, 106, 106, fg, 6)
        s.line(106, 82, 82, 106, fg, 6)
    elif kind == 'edit':
        s.path('M82 104L88 86L102 72L116 86L102 100Z', stroke=fg, fill='none', sw=5)
    elif kind == 'search':
        s.circle(90, 90, 9, fg, 'none', 5)
        s.line(98, 98, 110, 110, fg, 5)
    elif kind in ('upload', 'import'):
        s.line(94, 108, 94, 80, fg, 6)
        s.polyline([(82, 92), (94, 80), (106, 92)], fg, 'none', 6)
    elif kind in ('download', 'export'):
        s.line(94, 80, 94, 108, fg, 6)
        s.polyline([(82, 96), (94, 108), (106, 96)], fg, 'none', 6)
    elif kind == 'sync':
        s.path('M82 91Q86 78 99 82', stroke=fg, sw=5)
        s.polyline([(99, 74), (102, 84), (92, 84)], fg, 'none', 5)
        s.path('M106 98Q102 110 89 106', stroke=fg, sw=5)
        s.polyline([(89, 114), (86, 104), (96, 104)], fg, 'none', 5)
    elif kind == 'lock':
        s.rect(82, 92, 24, 16, rx=4, stroke=fg, fill='none', sw=4)
        s.path('M87 92V86Q87 78 94 78Q101 78 101 86V92', stroke=fg, sw=4)
    elif kind == 'unlock':
        s.rect(82, 92, 24, 16, rx=4, stroke=fg, fill='none', sw=4)
        s.path('M87 92V86Q87 78 94 78Q100 78 102 84', stroke=fg, sw=4)
    elif kind == 'warning':
        s.path('M94 78L110 106H78Z', stroke=fg, fill='none', sw=4)
        s.line(94, 88, 94, 98, fg, 4)
    elif kind == 'info':
        s.line(94, 91, 94, 106, fg, 5)
        s.circle(94, 82, 3, fg, fg, 1)
    elif kind == 'help':
        s.path('M86 86Q87 78 95 78Q103 78 104 86Q104 93 96 96V101', stroke=fg, sw=5)
        s.circle(96, 108, 2.8, fg, fg, 1)
    elif kind == 'star':
        s.polygon(star_points(94, 94, 15, 6), stroke=fg, fill='none', sw=4)
    elif kind == 'heart':
        s.path('M94 108L82 95Q76 88 82 82Q88 76 94 84Q100 76 106 82Q112 88 106 95Z', stroke=fg, fill='none', sw=4)
    elif kind == 'play':
        s.polygon([(88, 80), (108, 94), (88, 108)], stroke=fg, fill=fg, sw=2)
    elif kind == 'pause':
        s.line(88, 82, 88, 106, fg, 5)
        s.line(100, 82, 100, 106, fg, 5)
    elif kind == 'stop':
        s.rect(84, 84, 20, 20, rx=3, stroke=fg, fill='none', sw=4)
    elif kind == 'eye':
        s.path('M78 94Q94 78 110 94Q94 110 78 94Z', stroke=fg, fill='none', sw=4)
        s.circle(94, 94, 4, fg, 'none', 3)
    elif kind == 'slash':
        s.line(80, 108, 108, 80, fg, 6)
    elif kind == 'gear':
        s.circle(94, 94, 11, fg, 'none', 4)
        s.circle(94, 94, 3, fg, fg, 1)
    elif kind == 'share':
        s.circle(84, 94, 4, fg, fg, 1)
        s.circle(102, 82, 4, fg, fg, 1)
        s.circle(104, 106, 4, fg, fg, 1)
        s.line(88, 92, 99, 84, fg, 4)
        s.line(88, 96, 100, 104, fg, 4)
    elif kind == 'link':
        s.path('M85 92Q78 92 78 99Q78 106 85 106H93', stroke=fg, sw=4)
        s.path('M95 82H103Q110 82 110 89Q110 96 103 96H95', stroke=fg, sw=4)
        s.line(88, 94, 100, 94, fg, 4)
    elif kind in ('left', 'back'):
        s.line(84, 94, 108, 94, fg, 6)
        s.polyline([(94, 82), (82, 94), (94, 106)], fg, 'none', 6)
    elif kind in ('right', 'forward'):
        s.line(82, 94, 106, 94, fg, 6)
        s.polyline([(96, 82), (108, 94), (96, 106)], fg, 'none', 6)
    elif kind == 'up':
        s.line(94, 108, 94, 82, fg, 6)
        s.polyline([(82, 94), (94, 82), (106, 94)], fg, 'none', 6)
    elif kind == 'down':
        s.line(94, 82, 94, 108, fg, 6)
        s.polyline([(82, 96), (94, 108), (106, 96)], fg, 'none', 6)
    elif kind == 'code':
        s.polyline([(90, 83), (80, 94), (90, 105)], fg, 'none', 4)
        s.polyline([(98, 83), (108, 94), (98, 105)], fg, 'none', 4)
    elif kind == 'time':
        s.circle(94, 94, 13, fg, 'none', 4)
        s.line(94, 94, 94, 86, fg, 4)
        s.line(94, 94, 101, 98, fg, 4)
    elif kind == 'pin':
        s.path('M88 82L106 100M102 80L86 96M94 100L84 110', stroke=fg, sw=4)
    elif kind == 'copy':
        s.rect(82, 86, 18, 18, rx=2, stroke=fg, fill='none', sw=3)
        s.rect(90, 78, 18, 18, rx=2, stroke=fg, fill='none', sw=3)
    elif kind == 'brush':
        s.line(84, 104, 104, 84, fg, 5)
        s.path('M82 104Q78 110 88 110', stroke=fg, sw=4)
    elif kind == 'cloud':
        s.path('M82 100Q78 100 78 95Q78 90 84 90Q86 82 94 82Q102 82 104 90Q110 91 110 96Q110 100 104 100Z', stroke=fg, fill='none', sw=4)
    elif kind == 'user':
        s.circle(94, 86, 6, fg, 'none', 4)
        s.path('M82 108Q85 98 94 98Q103 98 106 108', stroke=fg, sw=4)
    else:
        s.line(94, 80, 94, 108, fg, 6)
        s.line(80, 94, 108, 94, fg, 6)


def draw_badge(s: Svg, kind: Optional[str]) -> None:
    if not kind:
        return
    fill = 'accent'
    if kind in ('warning',):
        fill = 'warning'
    elif kind in ('check', 'ok', 'apply'):
        fill = 'success'
    elif kind in ('close', 'error', 'delete', 'x'):
        fill = 'danger'
    badge_circle(s, fill)
    badge_symbol(s, kind)


def render_svg(entry: IconEntry, theme_name: Optional[str] = None, master: bool = False) -> str:
    theme = None if master else THEMES[theme_name or 'classic_gray']
    s = Svg(theme, entry.name.replace('_', ' '), master=master)
    draw_base(s, entry.base)
    # Some overlays need a small badge, but do not overlay direct one-glyph symbols.
    draw_badge(s, entry.overlay)
    return s.xml()

# ---------- Icon catalogue ----------

def build_entries() -> List[IconEntry]:
    entries: List[IconEntry] = []
    seen = set()

    def add(name: str, category: str, base: str, overlay: Optional[str] = None, *tags: str) -> None:
        name = safe(name)
        if name in seen:
            return
        seen.add(name)
        entries.append(IconEntry(name=name, category=category, base=base, overlay=overlay, tags=tuple(tags)))

    def group(prefix: str, category: str, base: str, actions: List[Tuple[str, Optional[str]]]) -> None:
        for suffix, overlay in actions:
            nm = prefix if suffix == '' else f'{prefix}_{suffix}'
            add(nm, category, base, overlay, prefix, suffix)

    common_actions = [
        ('', None), ('new', 'add'), ('add', 'add'), ('remove', 'remove'), ('delete', 'delete'),
        ('edit', 'edit'), ('search', 'search'), ('find', 'search'), ('check', 'check'), ('ok', 'check'),
        ('error', 'error'), ('warning', 'warning'), ('info', 'info'), ('help', 'help'), ('settings', 'gear'),
        ('properties', 'info'), ('favorite', 'star'), ('star', 'star'), ('pin', 'pin'), ('lock', 'lock'),
        ('unlock', 'unlock'), ('upload', 'upload'), ('download', 'download'), ('import', 'import'),
        ('export', 'export'), ('sync', 'sync'), ('refresh', 'sync'), ('share', 'share'), ('link', 'link'),
        ('copy', 'copy'), ('move', 'right'), ('preview', 'eye'), ('hide', 'slash'), ('history', 'time'),
        ('cloud', 'cloud'), ('user', 'user')
    ]

    file_extra = [
        ('open', 'up'), ('save', 'download'), ('save_as', 'edit'), ('print', 'down'), ('archive', 'down'),
        ('compress', 'down'), ('extract', 'up'), ('merge', 'link'), ('split', 'slash'), ('compare', 'eye'),
        ('template', 'star'), ('certificate', 'check'), ('signature', 'edit'), ('encrypt', 'lock'), ('decrypt', 'unlock'),
        ('local', 'pin'), ('bookmark', 'star'), ('code', 'code'), ('image', 'eye'), ('audio', 'play'),
        ('video', 'play'), ('table', 'grid'), ('database', 'cloud'), ('binary', 'gear'), ('text', 'info'),
        ('markdown', 'code'), ('script', 'code')
    ]
    group('file', 'file', 'file', common_actions + file_extra)
    group('document', 'file', 'file_stack', [('', None), ('stack', None), ('copy', 'copy'), ('merge', 'link'), ('split', 'slash'), ('compare', 'eye'), ('version', 'time'), ('review', 'check'), ('draft', 'edit'), ('publish', 'upload')])
    group('folder', 'folder', 'folder', common_actions + [('open', None), ('closed', None), ('root', 'pin'), ('home', 'user'), ('project', 'star'), ('library', 'grid'), ('backup', 'cloud'), ('temp', 'time'), ('mount', 'link'), ('share', 'share')])
    group('folder_open', 'folder', 'folder_open', [('', None), ('new', 'add'), ('search', 'search'), ('sync', 'sync'), ('warning', 'warning'), ('lock', 'lock'), ('upload', 'upload'), ('download', 'download')])

    # Common edit and clipboard operations.
    for nm, base, overlay in [
        ('cut', 'scissors', None), ('copy', 'copy', None), ('paste', 'clipboard', 'download'),
        ('clipboard', 'clipboard', None), ('clipboard_add', 'clipboard', 'add'), ('clipboard_check', 'clipboard', 'check'),
        ('clipboard_delete', 'clipboard', 'delete'), ('clipboard_search', 'clipboard', 'search'),
        ('undo', 'undo', None), ('redo', 'redo', None), ('eraser', 'pencil', 'slash'), ('pencil', 'pencil', None),
        ('edit', 'pencil', None), ('draw', 'brush', None), ('brush', 'brush', None), ('paint', 'palette', None),
        ('color_picker', 'palette', 'search'), ('fill_color', 'palette', 'download'), ('stroke_color', 'brush', 'edit'),
        ('crop', 'crop', None), ('selection', 'selection', None), ('select_all', 'selection', 'check'),
        ('select_none', 'selection', 'delete'), ('cursor', 'cursor', None), ('hand', 'hand', None),
        ('find', 'search', None), ('find_next', 'search', 'down'), ('find_previous', 'search', 'up'),
        ('replace', 'refresh', None), ('filter', 'filter', None), ('sort', 'sort', None), ('sort_ascending', 'sort', 'up'),
        ('sort_descending', 'sort', 'down'), ('tag', 'tag', None), ('tag_add', 'tag', 'add'),
        ('tag_remove', 'tag', 'remove'), ('bookmark', 'bookmark', None), ('bookmark_add', 'bookmark', 'add'),
        ('bookmark_remove', 'bookmark', 'remove'), ('flag', 'flag', None), ('flag_check', 'flag', 'check')
    ]:
        add(nm, 'edit', base, overlay)

    # Text formatting.
    text_items = [
        ('bold', 'bold', None), ('italic', 'italic', None), ('underline', 'underline', None),
        ('strikethrough', 'strikethrough', None), ('paragraph', 'paragraph', None), ('quote', 'quote', None),
        ('text', 'text', None), ('text_add', 'text', 'add'), ('text_remove', 'text', 'remove'),
        ('text_edit', 'text', 'edit'), ('text_search', 'text', 'search'), ('text_check', 'text', 'check'),
        ('text_color', 'text', 'brush'), ('text_highlight', 'text', 'star'), ('font', 'text', 'info'),
        ('font_size', 'text', 'up'), ('font_size_increase', 'text', 'add'), ('font_size_decrease', 'text', 'remove'),
        ('align_left', 'align_left', None), ('align_center', 'align_center', None), ('align_right', 'align_right', None),
        ('align_justify', 'align_justify', None), ('list_bulleted', 'list', None), ('list_numbered', 'list', 'info'),
        ('list_check', 'list', 'check'), ('list_add', 'list', 'add'), ('indent_increase', 'indent_increase', None),
        ('indent_decrease', 'indent_decrease', None), ('line_spacing', 'text', 'up'), ('letter_spacing', 'text', 'right'),
        ('word_wrap', 'text', 'sync'), ('text_direction_ltr', 'text', 'right'), ('text_direction_rtl', 'text', 'left'),
        ('superscript', 'superscript', None), ('subscript', 'subscript', None), ('clear_format', 'text', 'slash'),
        ('case_upper', 'text', 'up'), ('case_lower', 'text', 'down'), ('spell_check', 'text', 'check'),
        ('paragraph_spacing', 'paragraph', 'up'), ('insert_symbol', 'plus', None), ('insert_link', 'link', None),
        ('remove_link', 'unlink', None), ('insert_image', 'image', 'add'), ('insert_table', 'table', 'add'),
        ('insert_page_break', 'file', 'down'), ('insert_horizontal_rule', 'minus', None)
    ]
    for nm, base, overlay in text_items:
        add(nm, 'text', base, overlay)

    # Navigation and application windows.
    nav_items = [
        ('home', 'home', None), ('back', 'arrow_left', None), ('forward', 'arrow_right', None),
        ('up', 'arrow_up', None), ('down', 'arrow_down', None), ('arrow_left', 'arrow_left', None),
        ('arrow_right', 'arrow_right', None), ('arrow_up', 'arrow_up', None), ('arrow_down', 'arrow_down', None),
        ('chevron_left', 'chevron_left', None), ('chevron_right', 'chevron_right', None),
        ('chevron_up', 'chevron_up', None), ('chevron_down', 'chevron_down', None),
        ('refresh', 'refresh', None), ('reload', 'refresh', None), ('sync', 'refresh', 'sync'),
        ('stop_loading', 'close', None), ('menu', 'menu', None), ('hamburger_menu', 'menu', None),
        ('more_horizontal', 'ellipsis_h', None), ('more_vertical', 'ellipsis_v', None),
        ('grid_view', 'grid', None), ('list_view', 'list', None), ('table_view', 'table', None),
        ('details_view', 'list', 'info'), ('thumbnail_view', 'grid', 'image'), ('preview_pane', 'eye', None),
        ('hide_pane', 'eye', 'slash'), ('window', 'window', None), ('window_new', 'window', 'add'),
        ('window_close', 'window', 'close'), ('window_minimize', 'window', 'minus'), ('window_maximize', 'window', 'up'),
        ('window_restore', 'window', 'down'), ('window_fullscreen', 'window', 'up'), ('window_split', 'window', 'grid'),
        ('window_tile', 'window', 'grid'), ('window_cascade', 'window', 'copy'), ('tab', 'window', 'info'),
        ('tab_new', 'window', 'add'), ('tab_close', 'window', 'close'), ('tab_duplicate', 'window', 'copy'),
        ('tab_pin', 'window', 'pin'), ('sidebar', 'window', 'left'), ('panel_left', 'window', 'left'),
        ('panel_right', 'window', 'right'), ('panel_top', 'window', 'up'), ('panel_bottom', 'window', 'down'),
        ('browser', 'browser', None), ('browser_back', 'browser', 'left'), ('browser_forward', 'browser', 'right'),
        ('browser_refresh', 'browser', 'sync'), ('browser_home', 'browser', 'user'), ('browser_lock', 'browser', 'lock'),
        ('zoom_in', 'search', 'add'), ('zoom_out', 'search', 'remove'), ('zoom_reset', 'search', 'sync')
    ]
    for nm, base, overlay in nav_items:
        add(nm, 'navigation', base, overlay)

    # Media and creation.
    media_items = [
        ('play', 'play', None), ('pause', 'pause', None), ('stop', 'stop', None), ('record', 'record', None),
        ('previous', 'arrow_left', 'left'), ('next', 'arrow_right', 'right'), ('rewind', 'arrow_left', 'left'),
        ('fast_forward', 'arrow_right', 'right'), ('eject', 'arrow_up', 'up'), ('media_repeat', 'refresh', None),
        ('media_shuffle', 'refresh', 'random'), ('volume', 'speaker', None), ('volume_up', 'speaker', 'up'),
        ('volume_down', 'speaker', 'down'), ('volume_mute', 'speaker', 'slash'), ('microphone', 'microphone', None),
        ('microphone_mute', 'microphone', 'slash'), ('camera', 'camera', None), ('camera_add', 'camera', 'add'),
        ('camera_off', 'camera', 'slash'), ('image', 'image', None), ('image_add', 'image', 'add'),
        ('image_edit', 'image', 'edit'), ('image_remove', 'image', 'remove'), ('image_search', 'image', 'search'),
        ('video', 'video', None), ('video_add', 'video', 'add'), ('video_off', 'video', 'slash'),
        ('audio', 'audio', None), ('audio_add', 'audio', 'add'), ('playlist', 'list', 'play'),
        ('subtitles', 'text', 'info'), ('captions', 'text', 'info'), ('slideshow', 'image', 'play'),
        ('film', 'video', 'play'), ('snapshot', 'camera', 'check'), ('gallery', 'image', 'grid'),
        ('crop_image', 'crop', None), ('rotate_left', 'refresh', 'left'), ('rotate_right', 'refresh', 'right'),
        ('flip_horizontal', 'arrow_left', 'right'), ('flip_vertical', 'arrow_up', 'down')
    ]
    for nm, base, overlay in media_items:
        add(nm, 'media', base, overlay)

    # Data, development, devices, network, security.
    groups = [
        ('database', 'data', 'database'), ('server', 'data', 'server'), ('cloud', 'cloud', 'cloud'),
        ('network', 'network', 'network'), ('user', 'user', 'user'), ('group', 'user', 'group'),
        ('shield', 'security', 'shield'), ('key', 'security', 'key'), ('lock', 'security', 'lock'),
        ('calendar', 'time', 'calendar'), ('clock', 'time', 'clock'), ('monitor', 'device', 'monitor'),
        ('phone', 'device', 'phone'), ('tablet', 'device', 'tablet'), ('printer', 'device', 'printer'),
        ('keyboard', 'device', 'keyboard'), ('mouse', 'device', 'mouse'), ('cpu', 'device', 'cpu'),
        ('memory', 'device', 'memory'), ('disk', 'device', 'harddrive'), ('usb', 'device', 'usb'),
        ('battery', 'device', 'battery'), ('chart_bar', 'chart', 'chart_bar'), ('chart_line', 'chart', 'chart_line'),
        ('chart_pie', 'chart', 'pie'), ('gauge', 'chart', 'gauge'), ('terminal', 'development', 'terminal'),
        ('code', 'development', 'code'), ('bug', 'development', 'bug'), ('package', 'package', 'package'),
        ('box', 'package', 'box'), ('rocket', 'development', 'rocket'), ('globe', 'network', 'globe'),
        ('wifi', 'network', 'wifi'), ('bluetooth', 'network', 'bluetooth'), ('mail', 'communication', 'mail'),
        ('message', 'communication', 'message'), ('bell', 'communication', 'bell'), ('map', 'location', 'map'),
        ('location', 'location', 'location'), ('compass', 'location', 'compass'), ('book', 'help', 'book'),
        ('lightbulb', 'help', 'lightbulb'), ('power', 'system', 'power'), ('settings', 'system', 'gear'),
        ('wrench', 'tools', 'wrench'), ('hammer', 'tools', 'hammer'), ('sun', 'theme', 'sun'), ('moon', 'theme', 'moon'),
        ('heart', 'misc', 'heart'), ('star', 'misc', 'star'), ('warning', 'status', 'warning'), ('info', 'status', 'info'), ('help', 'status', 'help')
    ]
    small_actions = [('', None), ('add', 'add'), ('remove', 'remove'), ('delete', 'delete'), ('edit', 'edit'),
                     ('search', 'search'), ('check', 'check'), ('warning', 'warning'), ('info', 'info'),
                     ('lock', 'lock'), ('unlock', 'unlock'), ('upload', 'upload'), ('download', 'download'),
                     ('sync', 'sync'), ('share', 'share'), ('settings', 'gear')]
    for prefix, cat, base in groups:
        # Not every object needs all actions; add until catalogue limit later.
        group(prefix, cat, base, small_actions)

    # Status and miscellaneous direct symbols.
    for nm, base, overlay in [
        ('add', 'plus', None), ('remove', 'minus', None), ('delete', 'trash', None), ('close', 'close', None),
        ('check', 'check', None), ('ok', 'check', None), ('apply', 'check', None), ('cancel', 'close', None),
        ('error', 'close', None), ('question', 'help', None), ('about', 'info', None), ('favorite', 'star', None),
        ('not_favorite', 'star', 'slash'), ('like', 'heart', None), ('unlike', 'heart', 'slash'),
        ('flag_start', 'flag', None), ('flag_stop', 'flag', 'check'), ('notification', 'bell', None),
        ('notification_off', 'bell', 'slash'), ('bookmark_filled', 'bookmark', 'check'), ('pin', 'tag', 'pin'),
        ('unpin', 'tag', 'slash')
    ]:
        add(nm, 'status', base, overlay)

    # Keep exactly 500 icons.
    return entries[:500]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def make_preview(theme: str, entries: List[IconEntry]) -> None:
    size = 32
    cols = 25
    rows = math.ceil(len(entries) / cols)
    gap = 10
    margin = 12
    w = margin * 2 + cols * size + (cols - 1) * gap
    h = margin * 2 + rows * size + (rows - 1) * gap
    bg = (255, 255, 255, 255) if theme != 'graphite_dark_ui' else (31, 41, 55, 255)
    sheet = Image.new('RGBA', (w, h), bg)
    for i, e in enumerate(entries):
        x = margin + (i % cols) * (size + gap)
        y = margin + (i // cols) * (size + gap)
        p = ROOT / 'png' / theme / str(size) / f'{e.name}.png'
        im = Image.open(p).convert('RGBA')
        sheet.alpha_composite(im, (x, y))
    out = ROOT / 'preview' / f'{theme}_contact_sheet.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def make_html_preview(entries: List[IconEntry]) -> None:
    cards = []
    for e in entries:
        cards.append(f'<div class="card"><img src="../png/classic_gray/32/{e.name}.png" alt="{e.name}"><span>{e.name}</span></div>')
    css = '''
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;color:#1f2937;background:#fff;}
h1{font-size:22px} .meta{color:#667085} .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:8px;}
.card{display:flex;gap:8px;align-items:center;border:1px solid #e5e7eb;border-radius:8px;padding:8px;min-width:0;background:#fafafa;}
.card img{width:32px;height:32px;flex:0 0 32px}.card span{font-size:12px;overflow-wrap:anywhere;}
.theme-row{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 22px}.theme-row a{font-size:13px;}
'''
    html_text = '<!doctype html><html><head><meta charset="utf-8"><title>Neutrino Icon Pack Preview</title><style>' + css + '</style></head><body>'
    html_text += f'<h1>Neutrino Icon Pack Preview</h1><p class="meta">{len(entries)} original normalized icons, 5 themes, SVG plus PNG sizes 16, 24, 32, 48, 64, 128.</p>'
    html_text += '<div class="theme-row">' + ''.join(f'<a href="{t}_contact_sheet.png">{t} sheet</a>' for t in THEMES) + '</div>'
    html_text += '<div class="grid">' + ''.join(cards) + '</div></body></html>'
    write_text(ROOT / 'preview' / 'index.html', html_text)


def package() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    if TGZ_PATH.exists():
        TGZ_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(ROOT.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(ROOT.parent))
    with tarfile.open(TGZ_PATH, 'w:gz') as tar:
        tar.add(ROOT, arcname=ROOT.name)


def main() -> None:
    entries = build_entries()
    if len(entries) != 500:
        raise RuntimeError(f'Expected 500 icons, got {len(entries)}')
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)

    write_text(ROOT / 'themes.json', json.dumps(THEMES, indent=2))

    # Generate master variable SVG and themed fixed-color SVG + PNG. Render 128 first then downsample.
    for e in entries:
        master_svg = render_svg(e, master=True)
        write_text(ROOT / 'svg' / 'master' / f'{e.name}.svg', master_svg)

    for theme_name in THEMES:
        for e in entries:
            svg = render_svg(e, theme_name=theme_name, master=False)
            svg_path = ROOT / 'svg' / theme_name / f'{e.name}.svg'
            write_text(svg_path, svg)
            png128 = ROOT / 'png' / theme_name / '128' / f'{e.name}.png'
            png128.parent.mkdir(parents=True, exist_ok=True)
            cairosvg.svg2png(bytestring=svg.encode('utf-8'), write_to=str(png128), output_width=128, output_height=128)
            im128 = Image.open(png128).convert('RGBA')
            for sz in SIZES:
                out = ROOT / 'png' / theme_name / str(sz) / f'{e.name}.png'
                out.parent.mkdir(parents=True, exist_ok=True)
                if sz == 128:
                    continue
                im = im128.resize((sz, sz), Image.Resampling.LANCZOS)
                im.save(out)

    # Manifest files.
    manifest_json = []
    for e in entries:
        manifest_json.append({
            'name': e.name,
            'category': e.category,
            'base': e.base,
            'overlay': e.overlay,
            'tags': list(e.tags),
            'master_svg': f'svg/master/{e.name}.svg',
            'theme_svg_pattern': f'svg/{{theme}}/{e.name}.svg',
            'png_pattern': f'png/{{theme}}/{{size}}/{e.name}.png'
        })
    write_text(ROOT / 'manifest.json', json.dumps(manifest_json, indent=2))
    with (ROOT / 'manifest.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['name', 'category', 'base', 'overlay', 'tags', 'master_svg', 'theme_svg_pattern', 'png_pattern'])
        for e in entries:
            w.writerow([e.name, e.category, e.base, e.overlay or '', ';'.join(e.tags), f'svg/master/{e.name}.svg', f'svg/{{theme}}/{e.name}.svg', f'png/{{theme}}/{{size}}/{e.name}.png'])

    # C header for Neutrino integration.
    header_names = ',\n'.join(f'    "{e.name}"' for e in entries)
    header = f'''/* Auto-generated Neutrino icon manifest. Artwork: original generated SVG geometry. License: CC0-1.0 style public-domain dedication. */\n#ifndef NEUTRINO_ICONS_H\n#define NEUTRINO_ICONS_H\n\n#define NEUTRINO_ICON_COUNT {len(entries)}\nstatic const char* const NEUTRINO_ICON_NAMES[NEUTRINO_ICON_COUNT] = {{\n{header_names}\n}};\n\nstatic const int NEUTRINO_ICON_SIZES[] = {{16, 24, 32, 48, 64, 128}};\n#define NEUTRINO_ICON_THEME_COUNT {len(THEMES)}\nstatic const char* const NEUTRINO_ICON_THEMES[NEUTRINO_ICON_THEME_COUNT] = {{\n{', '.join('"'+t+'"' for t in THEMES)}\n}};\n\n#endif /* NEUTRINO_ICONS_H */\n'''
    write_text(ROOT / 'include' / 'neutrino_icons.h', header)

    readme = f'''# Neutrino Icon Pack CC0\n\nThis package contains **{len(entries)} original normalized system/UI icons** generated for the Neutrino project.\n\n## What is included\n\n- SVG master icons: `svg/master/*.svg`\n- Fixed-color themed SVGs: `svg/<theme>/*.svg`\n- PNG exports: `png/<theme>/<size>/*.png`\n- Sizes: {', '.join(map(str, SIZES))}\n- Themes: {', '.join(THEMES.keys())}\n- Manifest: `manifest.json` and `manifest.csv`\n- Neutrino C header: `include/neutrino_icons.h`\n- Preview contact sheets: `preview/*_contact_sheet.png` and `preview/index.html`\n- Regeneration script: `tools/generate_neutrino_icons.py`\n\n## Visual normalization rules\n\n- 128 x 128 SVG design grid\n- Transparent backgrounds\n- Rounded 8 px primary strokes with round caps and joins\n- Secondary detail strokes for internal structure\n- Consistent bottom-right action badges for add, delete, edit, search, upload, download, lock, warning, etc.\n- PNG exports are generated from the SVG masters, with the 128 px render downsampled for smaller sizes.\n\n## Recommended use\n\nFor toolbars, use 16 or 24 px. For palettes and trees, use 24 or 32 px. For splash/help/about screens, use 48, 64, or 128 px.\n\n## License\n\nThe icon artwork in this package is original generated geometry and is provided under the CC0-1.0 style public-domain dedication in `LICENSE.md`. No third-party icon artwork was imported.\n'''
    write_text(ROOT / 'README.md', readme)

    license_text = '''# License\n\nNeutrino Icon Pack CC0\n\nThe icon artwork, SVG geometry, themed SVG exports, PNG exports, manifests, and generator code in this package are provided under a CC0-1.0 style public-domain dedication to the extent possible.\n\nYou may copy, modify, distribute, recolor, embed, bundle, sell, sublicense, or use these icons for any purpose without attribution.\n\nNo third-party icon artwork was imported into this generated package. The icons were created as original geometric line-art from the generator script.\n\nSPDX-License-Identifier: CC0-1.0\n'''
    write_text(ROOT / 'LICENSE.md', license_text)

    notice = '''# Notice\n\nThis package was created for the Neutrino project from original generated SVG geometry.\n\nPublic-domain icon sources were considered, but the generated pack does not copy or bundle those external artworks. This keeps the pack visually consistent and avoids mixing licenses from multiple sources.\n\nThe generator emits consistent icon shapes, action badges, themed SVG files, and PNG exports.\n'''
    write_text(ROOT / 'NOTICE.md', notice)

    report = {
        'icon_count': len(entries),
        'themes': list(THEMES.keys()),
        'sizes': SIZES,
        'master_svg_count': len(list((ROOT / 'svg' / 'master').glob('*.svg'))),
        'themed_svg_count': sum(len(list((ROOT / 'svg' / t).glob('*.svg'))) for t in THEMES),
        'png_count': sum(len(list((ROOT / 'png' / t / str(sz)).glob('*.png'))) for t in THEMES for sz in SIZES),
    }
    write_text(ROOT / 'generation_report.json', json.dumps(report, indent=2))

    # Copy generator into package.
    tools = ROOT / 'tools'
    tools.mkdir(exist_ok=True)
    shutil.copy2(Path(__file__), tools / 'generate_neutrino_icons.py')

    for theme_name in THEMES:
        make_preview(theme_name, entries)
    make_html_preview(entries)
    package()
    print(json.dumps({
        'root': str(ROOT),
        'zip': str(ZIP_PATH),
        'tgz': str(TGZ_PATH),
        **report
    }, indent=2))

if __name__ == '__main__':
    main()
