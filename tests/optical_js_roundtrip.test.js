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

function makeImageData(width, height, fill = { r: 18, g: 25, b: 34 }) {
  const data = new Uint8ClampedArray(width * height * 4);
  for (let index = 0; index < width * height; index++) {
    data[index * 4] = fill.r;
    data[index * 4 + 1] = fill.g;
    data[index * 4 + 2] = fill.b;
    data[index * 4 + 3] = 255;
  }
  return { width, height, data };
}

function paintMatrix(imageData, matrix, bounds) {
  const cellW = bounds.width / QSOM.GRID_SIZE;
  const cellH = bounds.height / QSOM.GRID_SIZE;
  for (let row = 0; row < QSOM.GRID_SIZE; row++) {
    for (let col = 0; col < QSOM.GRID_SIZE; col++) {
      const bit = matrix[row][col];
      const color = bit ? oneCell(row, col) : { r: 246, g: 249, b: 252 };
      const x1 = Math.floor(bounds.x + col * cellW);
      const y1 = Math.floor(bounds.y + row * cellH);
      const x2 = Math.ceil(bounds.x + (col + 1) * cellW);
      const y2 = Math.ceil(bounds.y + (row + 1) * cellH);
      for (let y = y1; y < y2; y++) {
        for (let x = x1; x < x2; x++) {
          if (x < 0 || x >= imageData.width || y < 0 || y >= imageData.height) continue;
          const offset = (y * imageData.width + x) * 4;
          imageData.data[offset] = color.r;
          imageData.data[offset + 1] = color.g;
          imageData.data[offset + 2] = color.b;
          imageData.data[offset + 3] = 255;
        }
      }
    }
  }
}

const locatedFrame = QSOM.encodeOpticalFrames(payload)[0];
const imageData = makeImageData(820, 820);
paintMatrix(imageData, locatedFrame.matrix, { x: 192, y: 116, width: 436, height: 436 });
const locatedBounds = QSOM.detectOpticalBoundsFromImageData(imageData, { minFinderSize: 42, maxFinderSize: 92 });
assert(locatedBounds, "finder locator should find shifted/scaled optical code");
assert(locatedBounds.x > 140 && locatedBounds.x < 230, `unexpected located x ${locatedBounds.x}`);
assert(locatedBounds.y > 70 && locatedBounds.y < 150, `unexpected located y ${locatedBounds.y}`);
assert(locatedBounds.width > 380 && locatedBounds.width < 490, `unexpected located width ${locatedBounds.width}`);

console.log("optical JS adaptive threshold roundtrip passed");
