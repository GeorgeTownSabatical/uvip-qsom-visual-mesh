from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from uvip_qsom_visual_mesh.frames import make_frames, reassemble_frames
from uvip_qsom_visual_mesh.mcp_envelope import build_mcp_envelope
from uvip_qsom_visual_mesh.receiver import scan_path
from uvip_qsom_visual_mesh.visual import render_sphere_svg, render_wave_svg
from uvip_qsom_visual_mesh.optical import (
    decode_optical_frames,
    encode_optical_frames,
    interpret_repeated_matrices,
    matrix_to_frame,
    score_matrix,
    roundtrip_payload_bytes,
)


def test_mcp_envelope_frames_reassemble() -> None:
    payload = build_mcp_envelope(method="tools/list", params={"x": 1}, session_id="s", message_id="m")
    frames = make_frames(payload, frame_size=80)

    assert len(frames) > 1
    assert reassemble_frames(frames)
    assert frames[0]["parent_payload_hash"] == payload["payload_hash"]
    assert payload["allowed_methods"] == ["tools/list"]
    assert payload["policy_hint"] == "receiver-local-policy-required"
    assert payload["authorization_required"] is True
    assert payload["ttl_seconds"] == 300
    assert datetime.fromisoformat(payload["expires_at"]) > datetime.fromisoformat(payload["created_at"])


def test_mcp_envelope_accepts_bounded_policy_guidance() -> None:
    payload = build_mcp_envelope(
        method="tools/call",
        session_id="s",
        message_id="m",
        allowed_methods=["tools/list", "tools/call"],
        policy_hint="offline-review-only",
        ttl_seconds=60,
    )

    assert payload["allowed_methods"] == ["tools/list", "tools/call"]
    assert payload["policy_hint"] == "offline-review-only"
    assert payload["ttl_seconds"] == 60
    assert datetime.fromisoformat(payload["expires_at"]).tzinfo == timezone.utc


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
        assert report["authorization_required"] is True
        assert report["allowed_methods"] == ["tools/list"]
        assert report["policy_hint"] == "receiver-local-policy-required"
        assert report["ttl_seconds"] == 300
        assert report["expires_at"] == payload["expires_at"]


def test_receiver_detects_tampered_payload(tmp_path: Path) -> None:
    import json

    payload = build_mcp_envelope(method="tools/list", session_id="s", message_id="m")
    frames = make_frames(payload)
    payload["method"] = "tampered/method"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"payload": payload, "frames": frames}), encoding="utf-8")

    report = scan_path(manifest)

    assert report["valid"] is False
    assert report["authorization_required"] is True
    assert "Payload hash mismatch." in report["errors"]


def test_optical_codec_roundtrips_payload_bytes() -> None:
    payload = b'{"method":"tools/list","transport":"camera"}'

    assert roundtrip_payload_bytes(payload) == payload


def test_optical_frames_roundtrip_encoded_payload() -> None:
    encoded = "abcdefghijklmnopqrstuvwxyz0123456789" * 10
    frames = encode_optical_frames(encoded)
    decoded = decode_optical_frames([matrix_to_frame(frame.matrix) for frame in frames])

    assert decoded == encoded
    assert len(frames) > 1


def test_optical_matrix_scoring_accepts_clean_finders() -> None:
    frame = encode_optical_frames("abc123")[0]
    score = score_matrix(frame.matrix)

    assert score.acceptable is True
    assert score.finder_mismatches == 0
    assert score.finder_confidence == 1.0


def test_optical_matrix_scoring_rejects_bad_finders() -> None:
    frame = encode_optical_frames("abc123")[0]
    damaged = [row[:] for row in frame.matrix]
    for row in range(7):
        for col in range(7):
            damaged[row][col] = 1 - damaged[row][col]

    score = score_matrix(damaged)

    assert score.acceptable is False
    assert score.finder_mismatches > 0


def test_repeated_matrix_interpreter_repairs_single_capture_noise() -> None:
    frame = encode_optical_frames("abcdefghijklmnopqrstuvwxyz")[0]
    noisy_a = [row[:] for row in frame.matrix]
    noisy_b = [row[:] for row in frame.matrix]
    noisy_a[10][10] = 1 - noisy_a[10][10]
    noisy_b[12][12] = 1 - noisy_b[12][12]

    decoded = interpret_repeated_matrices([frame.matrix, noisy_a, noisy_b])

    assert decoded.data == frame.data
    assert decoded.frame_index == frame.frame_index
