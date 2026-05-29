from __future__ import annotations

from typing import Any

from .codec import chunk_text, encode_payload, payload_hash, utc_now


def make_frames(payload: dict[str, Any], *, frame_size: int = 512) -> list[dict[str, Any]]:
    encoded = encode_payload(payload)
    parts = chunk_text(encoded, frame_size)
    frames = []
    parent_hash = payload.get("payload_hash") or payload_hash(payload)
    for index, part in enumerate(parts):
        frame = {
            "schema": "uvip_qsom_visual_frame.v1",
            "protocol": "UVIP-QSOM-VISUAL",
            "created_at": utc_now(),
            "parent_payload_hash": parent_hash,
            "frame_index": index,
            "frame_count": len(parts),
            "encoding": "base64url-canonical-json",
            "symbol_mode": "wave-bar-sphere",
            "data": part,
        }
        frame["frame_hash"] = payload_hash(frame)
        frames.append(frame)
    return frames


def reassemble_frames(frames: list[dict[str, Any]]) -> str:
    ordered = sorted(frames, key=lambda row: int(row.get("frame_index", 0)))
    if not ordered:
        raise ValueError("No frames supplied.")
    expected = int(ordered[0].get("frame_count", 0))
    if len(ordered) != expected:
        raise ValueError(f"Expected {expected} frames, received {len(ordered)}.")
    for index, frame in enumerate(ordered):
        if int(frame.get("frame_index", -1)) != index:
            raise ValueError("Frame index sequence is incomplete.")
    return "".join(str(frame.get("data", "")) for frame in ordered)

