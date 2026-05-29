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

## Camera Optical Alpha

The browser optical transport adds:

- `41x41` high-contrast optical frame grid,
- three finder patterns,
- `QSOM` frame magic,
- frame version,
- frame index and count,
- payload length,
- CRC32 per frame,
- repeated animated transmission,
- browser camera receiver using `getUserMedia` and canvas sampling.

This is screen-to-camera alpha transport. It expects low perspective distortion and a centered sender square. Future versions should add perspective correction, adaptive thresholding, and stronger forward error correction.

## MCP Boundary

Decoded messages are untrusted input. A real MCP server must still apply:

- method allowlists,
- parameter validation,
- authentication/authorization outside the visual channel,
- rate limits,
- replay protection through `session_id`, `message_id`, and `nonce`.

## No Secrets

Visual payloads are observable by anyone who can see the screen or image. Do not encode tokens, private keys, credentials, recovery codes, or confidential records.
