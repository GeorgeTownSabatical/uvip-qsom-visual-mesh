from __future__ import annotations

import secrets
from typing import Any

from .codec import payload_hash, utc_now


def build_mcp_envelope(
    *,
    method: str,
    params: dict[str, Any] | None = None,
    sender_id: str = "uvip-qsom.sender.local",
    receiver_id: str = "mcp.server.visual.receiver",
    session_id: str | None = None,
    message_id: str | None = None,
    reply_channel_hint: str = "visual-return-frame",
    evidence_boundary: str = "Visual MCP envelope only; does not authorize tool execution by itself.",
) -> dict[str, Any]:
    payload = {
        "schema": "uvip_qsom_mcp_envelope.v1",
        "protocol": "UVIP-QSOM-MCP",
        "protocol_version": "0.1.0",
        "created_at": utc_now(),
        "session_id": session_id or f"session-{secrets.token_hex(8)}",
        "message_id": message_id or f"msg-{secrets.token_hex(8)}",
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "method": method,
        "params": params or {},
        "reply_channel_hint": reply_channel_hint,
        "nonce": secrets.token_hex(16),
        "evidence_boundary": evidence_boundary,
        "transport_boundary": "Visual-only transmission should be treated as untrusted input until decoded, hash-checked, and policy-authorized.",
    }
    payload["payload_hash"] = payload_hash(payload)
    return payload

