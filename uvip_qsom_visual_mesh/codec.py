from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_hash(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key not in {"payload_hash", "frame_hash"}}
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(text: str) -> bytes:
    compact = "".join(text.split())
    padding = "=" * (-len(compact) % 4)
    return base64.urlsafe_b64decode((compact + padding).encode("ascii"))


def encode_payload(payload: dict[str, Any]) -> str:
    return b64url_encode(canonical_json(payload).encode("utf-8"))


def decode_payload(encoded: str) -> dict[str, Any]:
    parsed = json.loads(b64url_decode(encoded).decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("Decoded payload is not a JSON object.")
    return parsed


def chunk_text(text: str, size: int) -> list[str]:
    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [text[index : index + size] for index in range(0, len(text), size)] or [""]

