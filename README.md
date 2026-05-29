# UVIP QSO Visual Mesh

Deterministic visual transport framework for carrying UVIP/QSO state and MCP message envelopes as colorful wave, bar, and sphere fields.

The framework is designed around a strict boundary:

```text
MCP envelope -> canonical payload -> hash -> visual frames -> receiver verification
```

The first implementation provides:

- canonical JSON hashing,
- MCP visual message envelopes,
- frame chunking and reassembly,
- wavy colorful barcode SVG rendering,
- sphere-field SVG rendering,
- HTML demo pages with embedded metadata,
- scanner/receiver support for JSON, SVG metadata, and HTML metadata,
- tamper detection through payload and frame hashes.
- browser alpha screen-to-camera optical transport.
- adaptive receiver thresholding calibrated from finder patterns.
- Python reference interpreter for finder confidence and repeated-frame majority voting.

## What It Is Not

This is not yet a camera-grade optical network. The current receiver decodes generated metadata and sidecar files. The visual image scanner is a planned next layer.

The reliable transport fallbacks remain:

- embedded SVG metadata,
- JSON sidecars,
- base64url frame payloads,
- normal URL/QR fallback where needed.

## Quick Demo

```bash
python scripts/uvip_qsom_demo.py --output-dir examples/demo
python scripts/uvip_qsom_scan.py examples/demo/manifest.json --strict
python scripts/uvip_qsom_scan.py examples/demo/sphere_field.svg --strict
python scripts/uvip_qsom_scan.py examples/demo/index.html --strict
```

Open:

```text
examples/demo/index.html
```

Camera optical alpha:

```text
https://georgetownsabatical.github.io/uvip-qsom-visual-mesh/optical-network/
```

The optical page includes a sender, camera receiver, and still-canvas validation path.

Air-gapped operation:

```text
AI / MCP client A -> screen frames -> camera -> AI / MCP receiver B
```

The machines do not need internet access or the same network. They only need a visual line-of-sight path. Decoded messages remain untrusted until the receiver validates hashes and authorizes the MCP method.

## MCP Visual Envelope

The payload carries enough information for an MCP-style message exchange:

- protocol version,
- session id,
- sender and receiver ids,
- message id,
- method,
- params,
- sequence and frame counts,
- reply channel hint,
- nonce,
- timestamp,
- evidence boundary,
- payload hash.

Do not put secrets, private keys, credentials, or live bearer tokens into visual payloads.

## Evidence Boundary

UVIP/QSOM visual frames can attest that a specific message envelope was produced and has not changed. They do not prove external facts or authorize an MCP server by themselves.
