from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .codec import decode_payload, payload_hash, utc_now
from .frames import reassemble_frames


def _metadata_report(path: Path, source_kind: str, metadata: dict[str, Any]) -> dict[str, Any]:
    payload = metadata.get("payload", {})
    frames = metadata.get("frames", [])
    errors: list[str] = []
    if not isinstance(payload, dict):
        errors.append("Metadata payload is not an object.")
        payload = {}
    if not isinstance(frames, list):
        errors.append("Metadata frames are not an array.")
        frames = []
    computed = payload_hash(payload) if payload else ""
    declared = str(payload.get("payload_hash") or "")
    if declared and computed != declared:
        errors.append("Payload hash mismatch.")
    try:
        encoded = reassemble_frames([frame for frame in frames if isinstance(frame, dict)])
        decoded = decode_payload(encoded)
        if decoded.get("payload_hash") != declared:
            errors.append("Reassembled frame payload hash does not match metadata payload.")
    except Exception as exc:  # noqa: BLE001 - receiver reports decode failures.
        errors.append(f"Frame reassembly failed: {exc}")
    return {
        "schema": "uvip_qsom_visual_scan_report.v1",
        "scanned_at": utc_now(),
        "source_path": str(path),
        "source_kind": source_kind,
        "valid": not errors,
        "payload_hash": declared,
        "computed_payload_hash": computed,
        "method": payload.get("method", ""),
        "session_id": payload.get("session_id", ""),
        "message_id": payload.get("message_id", ""),
        "sender_id": payload.get("sender_id", ""),
        "receiver_id": payload.get("receiver_id", ""),
        "authorization_required": True,
        "allowed_methods": payload.get("allowed_methods", []),
        "policy_hint": payload.get("policy_hint", ""),
        "ttl_seconds": payload.get("ttl_seconds", ""),
        "expires_at": payload.get("expires_at", ""),
        "frame_count": len(frames),
        "errors": errors,
        "transport_boundary": "Decoded visual input is untrusted until caller authorizes the MCP method and params.",
        "payload": payload,
    }


def _load_json(path: Path) -> dict[str, Any]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("JSON source is not an object.")
    return parsed


def _load_svg_metadata(path: Path) -> dict[str, Any]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    for element in root.iter():
        if element.tag.endswith("metadata") and element.attrib.get("id") == "uvip-qsom-visual-payload":
            parsed = json.loads(html.unescape("".join(element.itertext()).strip()))
            if not isinstance(parsed, dict):
                raise ValueError("SVG metadata is not an object.")
            return parsed
    raise ValueError("SVG metadata id uvip-qsom-visual-payload not found.")


def _load_html_metadata(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="uvip-qsom-visual-payload">(.*?)</script>', text, re.DOTALL)
    if not match:
        raise ValueError("HTML visual payload script tag not found.")
    parsed = json.loads(html.unescape(match.group(1).strip()))
    if not isinstance(parsed, dict):
        raise ValueError("HTML metadata is not an object.")
    return parsed


def scan_path(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            metadata = _load_json(path)
            if "payload" not in metadata:
                metadata = {"payload": metadata, "frames": []}
            return _metadata_report(path, "json_metadata", metadata)
        if suffix == ".svg":
            return _metadata_report(path, "svg_metadata", _load_svg_metadata(path))
        if suffix in {".html", ".htm"}:
            return _metadata_report(path, "html_metadata", _load_html_metadata(path))
    except Exception as exc:  # noqa: BLE001 - scanner reports all failures.
        return {
            "schema": "uvip_qsom_visual_scan_report.v1",
            "scanned_at": utc_now(),
            "source_path": str(path),
            "source_kind": "decode_error",
            "valid": False,
            "payload_hash": "",
            "computed_payload_hash": "",
            "method": "",
            "session_id": "",
            "message_id": "",
            "sender_id": "",
            "receiver_id": "",
            "authorization_required": True,
            "allowed_methods": [],
            "policy_hint": "",
            "ttl_seconds": "",
            "expires_at": "",
            "frame_count": 0,
            "errors": [str(exc)],
            "transport_boundary": "Decode failed before MCP authorization.",
            "payload": {},
        }
    raise ValueError(f"Unsupported scan path: {path}")
