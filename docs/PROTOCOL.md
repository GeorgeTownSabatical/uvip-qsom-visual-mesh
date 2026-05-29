# UVIP/QSOM Visual MCP Protocol

## Purpose

Carry MCP-style message envelopes through deterministic visual artifacts.

```text
MCP envelope
-> canonical JSON
-> payload hash
-> base64url frame chunks
-> wave barcode / sphere field
-> receiver metadata scan
-> hash verification
-> caller policy authorization
```

## Visual Modes

### Wave Barcode

Colorful sinusoidal bars derived from the payload hash.

### Sphere Field

Colorful 2D projected spheres derived from the same payload hash. The sphere field is intended to evolve into a screen-to-camera visual transport where each sphere can carry frame position, channel, and timing information.

## Receiver Contract

The receiver currently decodes:

- `manifest.json`,
- SVG `<metadata id="uvip-qsom-visual-payload">`,
- HTML `<script type="application/json" id="uvip-qsom-visual-payload">`.

It validates:

- payload hash,
- frame sequence completeness,
- reassembled frame payload hash.

## MCP Boundary

Decoded messages are untrusted input. A real MCP server must still apply:

- method allowlists,
- parameter validation,
- authentication/authorization outside the visual channel,
- rate limits,
- replay protection through `session_id`, `message_id`, and `nonce`.

## No Secrets

Visual payloads are observable by anyone who can see the screen or image. Do not encode tokens, private keys, credentials, recovery codes, or confidential records.

