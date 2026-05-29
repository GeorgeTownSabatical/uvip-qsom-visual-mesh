# Air-Gapped Visual AI Communication

UVIP/QSOM optical networking is designed for agents that are not connected to the internet and are not on the same network.

The required link is visual:

```text
AI / MCP client A
-> screen-rendered UVIP/QSOM optical frames
-> camera or screen capture
-> AI / MCP receiver B
-> decode, hash-check, authorize
```

## What This Enables

- Offline agent-to-agent message transfer.
- Air-gapped MCP request handoff.
- Visual transfer across machines with no shared Wi-Fi, LAN, Bluetooth, or cable.
- Human-observable communication where every transmitted payload can be displayed, logged, and verified.

## What It Still Requires

- A display on the sender side.
- A camera or screen-capture path on the receiver side.
- Enough frame visibility for the receiver to sample the optical grid.
- Receiver-side policy authorization before any decoded MCP method is executed.

## Security Model

The visual channel provides transport, not trust.

Decoded frames must still pass:

- frame magic/version checks,
- sequence completeness checks,
- per-frame CRC checks,
- payload hash checks,
- replay checks using `session_id`, `message_id`, and `nonce`,
- MCP method allowlists,
- parameter validation,
- local authorization policy.

## No Secrets

Visual frames are observable by anyone who can see the display or camera feed. Do not transmit:

- passwords,
- private keys,
- bearer tokens,
- recovery codes,
- confidential records.

## Practical Use

1. Sender opens:

```text
docs/optical-network/index.html
```

2. Sender starts optical transmission.
3. Receiver opens the same page and starts camera receiver.
4. Receiver points camera at sender display.
5. Receiver reconstructs the MCP envelope and presents it for authorization.

This allows disconnected systems to exchange structured messages without a network path.

