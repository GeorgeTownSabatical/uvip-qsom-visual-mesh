const assert = require("assert");

if (typeof globalThis.btoa === "undefined") {
  globalThis.btoa = value => Buffer.from(value, "binary").toString("base64");
}

if (typeof globalThis.atob === "undefined") {
  globalThis.atob = value => Buffer.from(value, "base64").toString("binary");
}

const QSOM = require("../docs/optical-network/optical.js");

function zeroCell(row, col) {
  const wobble = (row * 7 + col * 11) % 15;
  return { r: 162 + wobble, g: 174 + Math.floor(wobble / 2), b: 186 + (wobble % 5) };
}

function oneCell(row, col) {
  const palette = [
    { r: 24, g: 88, b: 172 },
    { r: 142, g: 52, b: 134 },
    { r: 34, g: 128, b: 92 },
    { r: 172, g: 72, b: 30 }
  ];
  return palette[(row + col) % palette.length];
}

function syntheticSamples(matrix) {
  return matrix.map((row, rowIndex) =>
    row.map((bit, colIndex) => (bit ? oneCell(rowIndex, colIndex) : zeroCell(rowIndex, colIndex)))
  );
}

const payload = {
  schema: "uvip_qsom_camera_mcp_envelope.v1",
  protocol: "UVIP-QSOM-CAMERA-MCP",
  method: "tools/list",
  params: {
    transport: "camera-grade-optical-alpha",
    note: "adaptive threshold test over non-white cells"
  }
};

const decodedFrames = new Map();
for (const frame of QSOM.encodeOpticalFrames(payload)) {
  const sampled = QSOM.cellSamplesToMatrix(syntheticSamples(frame.matrix));
  const decoded = QSOM.frameFromMatrix(sampled);
  decodedFrames.set(decoded.index, decoded);
}

assert.deepStrictEqual(QSOM.decodeOpticalFrames(decodedFrames), payload);

const fixedThresholdWouldMisreadZero = zeroCell(0, 1);
const fixedLuminance =
  0.2126 * fixedThresholdWouldMisreadZero.r +
  0.7152 * fixedThresholdWouldMisreadZero.g +
  0.0722 * fixedThresholdWouldMisreadZero.b;
assert(fixedLuminance < 190, "test background must be below the old fixed white threshold");

console.log("optical JS adaptive threshold roundtrip passed");
