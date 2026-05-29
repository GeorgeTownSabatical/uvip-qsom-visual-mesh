# Camera-Grade Optical Networking Alpha

This page upgrades UVIP/QSOM from static metadata scanning to screen-to-camera frame transport.

It is meant for air-gapped communication:

```text
offline sender screen -> receiver camera -> decoded MCP envelope
```

The sender and receiver do not need internet, LAN, Wi-Fi, Bluetooth, or a cable.

## Live Page

```text
https://georgetownsabatical.github.io/uvip-qsom-visual-mesh/optical-network/
```

## Current Capabilities

- Browser sender renders animated high-contrast optical frames.
- Browser receiver uses `getUserMedia`, canvas sampling, finder-calibrated adaptive thresholding, and frame checksums.
- MCP envelope is split into optical frames and reconstructed after all frames are captured.
- Still-canvas mode validates the codec without a camera.
- Python reference interpreter scores finder confidence and can majority-vote repeated captures of the same frame.

## Physical Use

1. Open the optical-network page on two devices.
2. On the sender device, press `Start Sender`.
3. On the receiver device, press `Start Camera Receiver`.
4. Point the receiver camera at the sender square.
5. Keep the sender square centered and as flat as possible.

## Boundary

This is an alpha optical receiver. It assumes the sender square mostly fills the receiver guide and is not heavily rotated or warped. It validates frame magic, version, finder confidence, sequence, payload length, and CRC32 before reconstructing the MCP envelope.

Decoded messages are still untrusted input. An MCP server must independently authorize method and params.
