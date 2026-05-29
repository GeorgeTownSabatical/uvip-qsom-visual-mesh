from __future__ import annotations

import html
import json
from typing import Any

from .codec import canonical_json


def render_demo_html(payload: dict[str, Any], frames: list[dict[str, Any]]) -> str:
    metadata = {"payload": payload, "frames": frames}
    metadata_json = html.escape(canonical_json(metadata))
    payload_json = html.escape(json.dumps(payload, indent=2, sort_keys=True))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UVIP QSO Visual Mesh Demo</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #162033; background: #f8fbff; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 20px; }}
    h1 {{ font-size: clamp(32px, 5vw, 58px); margin: 0 0 8px; letter-spacing: 0; }}
    .lead {{ color: #536173; font-size: 18px; max-width: 850px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 20px 0; }}
    .panel {{ background: #fff; border: 1px solid #d8dee6; border-radius: 8px; padding: 14px; }}
    iframe {{ width: 100%; min-height: 420px; border: 0; background: white; }}
    pre {{ overflow-x: auto; max-height: 360px; padding: 12px; border-radius: 8px; background: #101820; color: #f8fbff; }}
    code {{ background: #edf1f5; border-radius: 4px; padding: 2px 5px; }}
    @media (max-width: 840px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>UVIP QSO Visual Mesh Demo</h1>
    <p class="lead">A visual-only MCP envelope prototype. Wave and sphere renderings carry the same payload in embedded metadata and frame sidecars.</p>
    <script type="application/json" id="uvip-qsom-visual-payload">{metadata_json}</script>
    <div class="grid">
      <section class="panel">
        <h2>Sphere Field</h2>
        <iframe src="sphere_field.svg" title="UVIP QSO sphere field"></iframe>
      </section>
      <section class="panel">
        <h2>Wave Barcode</h2>
        <iframe src="wave_barcode.svg" title="UVIP QSO wave barcode"></iframe>
      </section>
    </div>
    <section class="panel">
      <h2>MCP Envelope</h2>
      <p><strong>Method:</strong> <code>{html.escape(str(payload.get("method", "")))}</code></p>
      <p><strong>Payload Hash:</strong> <code>{html.escape(str(payload.get("payload_hash", "")))}</code></p>
      <p><strong>Boundary:</strong> {html.escape(str(payload.get("transport_boundary", "")))}</p>
      <pre>{payload_json}</pre>
    </section>
  </main>
</body>
</html>
"""

