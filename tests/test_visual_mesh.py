from __future__ import annotations

from pathlib import Path

from uvip_qsom_visual_mesh.frames import make_frames, reassemble_frames
from uvip_qsom_visual_mesh.mcp_envelope import build_mcp_envelope
from uvip_qsom_visual_mesh.receiver import scan_path
from uvip_qsom_visual_mesh.visual import render_sphere_svg, render_wave_svg


def test_mcp_envelope_frames_reassemble() -> None:
    payload = build_mcp_envelope(method="tools/list", params={"x": 1}, session_id="s", message_id="m")
    frames = make_frames(payload, frame_size=80)

    assert len(frames) > 1
    assert reassemble_frames(frames)
    assert frames[0]["parent_payload_hash"] == payload["payload_hash"]


def test_wave_and_sphere_embed_metadata() -> None:
    payload = build_mcp_envelope(method="tools/list", session_id="s", message_id="m")
    frames = make_frames(payload)

    wave = render_wave_svg(payload, frames)
    sphere = render_sphere_svg(payload, frames)

    assert "uvip-qsom-visual-payload" in wave
    assert "UVIP-QSOM-WAVE" in wave
    assert "uvip-qsom-visual-payload" in sphere
    assert "UVIP-QSOM-SPHERE" in sphere
    assert wave != sphere


def test_receiver_scans_manifest_svg_and_html(tmp_path: Path) -> None:
    from uvip_qsom_visual_mesh.html_demo import render_demo_html
    import json

    payload = build_mcp_envelope(method="tools/list", session_id="s", message_id="m")
    frames = make_frames(payload)
    metadata = {"payload": payload, "frames": frames}
    manifest = tmp_path / "manifest.json"
    svg = tmp_path / "sphere.svg"
    html = tmp_path / "index.html"
    manifest.write_text(json.dumps(metadata), encoding="utf-8")
    svg.write_text(render_sphere_svg(payload, frames), encoding="utf-8")
    html.write_text(render_demo_html(payload, frames), encoding="utf-8")

    for path in [manifest, svg, html]:
        report = scan_path(path)
        assert report["valid"] is True
        assert report["payload_hash"] == payload["payload_hash"]
        assert report["method"] == "tools/list"


def test_receiver_detects_tampered_payload(tmp_path: Path) -> None:
    import json

    payload = build_mcp_envelope(method="tools/list", session_id="s", message_id="m")
    frames = make_frames(payload)
    payload["method"] = "tampered/method"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"payload": payload, "frames": frames}), encoding="utf-8")

    report = scan_path(manifest)

    assert report["valid"] is False
    assert "Payload hash mismatch." in report["errors"]

