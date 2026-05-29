#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uvip_qsom_visual_mesh.frames import make_frames
from uvip_qsom_visual_mesh.html_demo import render_demo_html
from uvip_qsom_visual_mesh.mcp_envelope import build_mcp_envelope
from uvip_qsom_visual_mesh.visual import render_sphere_svg, render_wave_svg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a UVIP/QSO visual MCP demo.")
    parser.add_argument("--output-dir", default="examples/demo")
    parser.add_argument("--method", default="tools/list")
    parser.add_argument("--receiver-id", default="mcp.server.visual.receiver")
    parser.add_argument("--sender-id", default="uvip-qsom.sender.local")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_mcp_envelope(
        method=args.method,
        params={
            "transport": "visual-only",
            "requested_capability": "mcp_message_exchange",
            "safety": "no secrets; receiver must authorize decoded methods",
        },
        sender_id=args.sender_id,
        receiver_id=args.receiver_id,
    )
    frames = make_frames(payload, frame_size=420)
    metadata = {"payload": payload, "frames": frames}
    (output_dir / "manifest.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "sphere_field.svg").write_text(render_sphere_svg(payload, frames), encoding="utf-8")
    (output_dir / "wave_barcode.svg").write_text(render_wave_svg(payload, frames), encoding="utf-8")
    (output_dir / "index.html").write_text(render_demo_html(payload, frames), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "payload_hash": payload["payload_hash"], "frame_count": len(frames)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

