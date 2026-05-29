from __future__ import annotations

import hashlib
import html
import json
import math
from typing import Any

from .codec import canonical_json


def digest_stream(seed: str, length: int) -> bytes:
    chunks: list[bytes] = []
    counter = 0
    while sum(len(chunk) for chunk in chunks) < length:
        chunks.append(hashlib.sha256(f"{seed}:{counter}".encode("utf-8")).digest())
        counter += 1
    return b"".join(chunks)[:length]


def hsl(a: int, b: int, c: int, *, offset: int = 0) -> str:
    hue = ((a * 360) // 255 + offset) % 360
    saturation = 55 + (b % 38)
    light = 36 + (c % 28)
    return f"hsl({hue} {saturation}% {light}%)"


def svg_metadata(payload: dict[str, Any], frames: list[dict[str, Any]]) -> str:
    metadata = {
        "payload": payload,
        "frames": frames,
        "scanner_boundary": "Decode SVG metadata or frame sidecars first; camera image decoding is not implemented in v0.1.",
    }
    return html.escape(canonical_json(metadata))


def render_wave_svg(payload: dict[str, Any], frames: list[dict[str, Any]], *, size: int = 960, modules: int = 41) -> str:
    seed = str(payload.get("payload_hash") or "")
    stream = digest_stream(seed, modules * modules * 5)
    cell = size / modules
    marks: list[str] = []
    for row in range(modules):
        for col in range(modules):
            offset = (row * modules + col) * 5
            a, b, c, d, e = stream[offset : offset + 5]
            if (a ^ c) % 100 < 28:
                continue
            x = col * cell
            base_y = row * cell
            amp = (d % 11) / 10 * cell * 0.35
            phase = (e / 255) * math.tau
            y1 = base_y + cell * 0.22 + math.sin(col * 0.72 + phase) * amp
            y2 = base_y + cell * 0.78 + math.cos(col * 0.51 + phase) * amp
            marks.append(
                f'<path d="M{x:.2f},{y1:.2f} C{x + cell * .35:.2f},{base_y:.2f} {x + cell * .65:.2f},{base_y + cell:.2f} {x + cell:.2f},{y2:.2f}" '
                f'stroke="{hsl(a, b, c)}" stroke-width="{max(2.0, cell * .38):.2f}" stroke-linecap="round" opacity=".82"/>'
            )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img">
  <metadata id="uvip-qsom-visual-payload" data-encoding="json">{svg_metadata(payload, frames)}</metadata>
  <rect width="100%" height="100%" fill="#f8fbff"/>
  <g>{''.join(marks)}</g>
  <text x="{cell:.2f}" y="{size - cell:.2f}" font-family="monospace" font-size="{cell * .72:.2f}" fill="#334155">UVIP-QSOM-WAVE {seed[:18]}</text>
</svg>
"""


def render_sphere_svg(payload: dict[str, Any], frames: list[dict[str, Any]], *, width: int = 1280, height: int = 720, spheres: int = 96) -> str:
    seed = str(payload.get("payload_hash") or "")
    stream = digest_stream(seed, spheres * 9)
    marks: list[str] = []
    for index in range(spheres):
        a, b, c, d, e, f, g, h, i = stream[index * 9 : index * 9 + 9]
        x = 72 + (a / 255) * (width - 144)
        y = 72 + (b / 255) * (height - 144)
        radius = 12 + (c % 54)
        color = hsl(d, e, f, offset=index * 7)
        shadow = hsl(g, h, i, offset=180)
        opacity = 0.48 + ((a ^ i) % 42) / 100
        marks.append(
            f'<g opacity="{opacity:.2f}">'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="{color}"/>'
            f'<circle cx="{x - radius * .32:.2f}" cy="{y - radius * .35:.2f}" r="{radius * .34:.2f}" fill="#ffffff" opacity=".38"/>'
            f'<circle cx="{x + radius * .18:.2f}" cy="{y + radius * .22:.2f}" r="{radius * .52:.2f}" fill="{shadow}" opacity=".24"/>'
            f'</g>'
        )
    links: list[str] = []
    for index in range(0, min(spheres - 1, 48), 2):
        a, b, c, d = stream[index * 9 : index * 9 + 4]
        x1 = 72 + (a / 255) * (width - 144)
        y1 = 72 + (b / 255) * (height - 144)
        x2 = 72 + (c / 255) * (width - 144)
        y2 = 72 + (d / 255) * (height - 144)
        links.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#64748b" stroke-width="1.2" opacity=".22"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <metadata id="uvip-qsom-visual-payload" data-encoding="json">{svg_metadata(payload, frames)}</metadata>
  <rect width="100%" height="100%" fill="#06121f"/>
  <g>{''.join(links)}</g>
  <g>{''.join(marks)}</g>
  <text x="28" y="{height - 28}" font-family="monospace" font-size="18" fill="#dbeafe">UVIP-QSOM-SPHERE {seed[:24]}</text>
</svg>
"""

