const QSOM = (() => {
  const GRID_SIZE = 41;
  const FINDER_SIZE = 7;
  const MAX_DATA_BYTES = 128;
  const MAGIC = [0x51, 0x53, 0x4f, 0x4d]; // QSOM
  const VERSION = 1;

  function b64urlFromBytes(bytes) {
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
  }

  function bytesFromB64url(text) {
    const padded = text.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (text.length % 4)) % 4);
    const binary = atob(padded);
    return Uint8Array.from(binary, char => char.charCodeAt(0));
  }

  function utf8Bytes(text) {
    return new TextEncoder().encode(text);
  }

  function utf8Text(bytes) {
    return new TextDecoder().decode(bytes);
  }

  function crc32(bytes) {
    let crc = 0xffffffff;
    for (const byte of bytes) {
      crc ^= byte;
      for (let i = 0; i < 8; i++) {
        crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
      }
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function isFinderCell(row, col) {
    const inLeft = col < FINDER_SIZE;
    const inRight = col >= GRID_SIZE - FINDER_SIZE;
    const inTop = row < FINDER_SIZE;
    const inBottom = row >= GRID_SIZE - FINDER_SIZE;
    return (inTop && inLeft) || (inTop && inRight) || (inBottom && inLeft);
  }

  function dataPositions() {
    const positions = [];
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        if (!isFinderCell(row, col)) positions.push([row, col]);
      }
    }
    return positions;
  }

  const POSITIONS = dataPositions();

  function finderValue(row, col) {
    if (row === 0 || row === 6 || col === 0 || col === 6) return 1;
    if (row === 1 || row === 5 || col === 1 || col === 5) return 0;
    return 1;
  }

  function expectedFinderValue(row, col) {
    if (row < FINDER_SIZE && col < FINDER_SIZE) return finderValue(row, col);
    if (row < FINDER_SIZE && col >= GRID_SIZE - FINDER_SIZE) return finderValue(row, col - (GRID_SIZE - FINDER_SIZE));
    if (row >= GRID_SIZE - FINDER_SIZE && col < FINDER_SIZE) return finderValue(row - (GRID_SIZE - FINDER_SIZE), col);
    return null;
  }

  function bytesToBits(bytes) {
    const bits = [];
    for (const byte of bytes) {
      for (let shift = 7; shift >= 0; shift--) bits.push((byte >> shift) & 1);
    }
    return bits;
  }

  function bitsToBytes(bits) {
    const out = [];
    for (let index = 0; index + 7 < bits.length; index += 8) {
      let value = 0;
      for (const bit of bits.slice(index, index + 8)) value = (value << 1) | (bit & 1);
      out.push(value);
    }
    return Uint8Array.from(out);
  }

  function writeUint16(bytes, offset, value) {
    bytes[offset] = (value >> 8) & 255;
    bytes[offset + 1] = value & 255;
  }

  function writeUint32(bytes, offset, value) {
    bytes[offset] = (value >>> 24) & 255;
    bytes[offset + 1] = (value >>> 16) & 255;
    bytes[offset + 2] = (value >>> 8) & 255;
    bytes[offset + 3] = value & 255;
  }

  function readUint16(bytes, offset) {
    return (bytes[offset] << 8) | bytes[offset + 1];
  }

  function readUint32(bytes, offset) {
    return (((bytes[offset] << 24) >>> 0) | (bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3]) >>> 0;
  }

  function encodeFrameBytes(index, count, data) {
    const checksum = crc32(data);
    const header = new Uint8Array(15 + data.length);
    header.set(MAGIC, 0);
    header[4] = VERSION;
    writeUint16(header, 5, index);
    writeUint16(header, 7, count);
    writeUint16(header, 9, data.length);
    writeUint32(header, 11, checksum);
    header.set(data, 15);
    return header;
  }

  function decodeFrameBytes(raw) {
    if (raw.length < 15) throw new Error("Frame shorter than header");
    if (!MAGIC.every((byte, index) => raw[index] === byte)) throw new Error("Bad frame magic");
    if (raw[4] !== VERSION) throw new Error("Unsupported frame version");
    const index = readUint16(raw, 5);
    const count = readUint16(raw, 7);
    const length = readUint16(raw, 9);
    const checksum = readUint32(raw, 11);
    const data = raw.slice(15, 15 + length);
    if (data.length !== length) throw new Error("Frame payload truncated");
    if (crc32(data) !== checksum) throw new Error("Frame checksum mismatch");
    return { index, count, data, checksum };
  }

  function matrixFromFrame(index, count, data) {
    const raw = encodeFrameBytes(index, count, data);
    const bits = bytesToBits(raw);
    if (bits.length > POSITIONS.length) throw new Error("Frame does not fit");
    const matrix = Array.from({ length: GRID_SIZE }, () => Array(GRID_SIZE).fill(0));
    for (const [startRow, startCol] of [[0, 0], [0, GRID_SIZE - FINDER_SIZE], [GRID_SIZE - FINDER_SIZE, 0]]) {
      for (let row = 0; row < FINDER_SIZE; row++) {
        for (let col = 0; col < FINDER_SIZE; col++) matrix[startRow + row][startCol + col] = finderValue(row, col);
      }
    }
    bits.forEach((bit, i) => {
      const [row, col] = POSITIONS[i];
      matrix[row][col] = bit;
    });
    return matrix;
  }

  function frameFromMatrix(matrix) {
    const bits = POSITIONS.map(([row, col]) => matrix[row][col] ? 1 : 0);
    return decodeFrameBytes(bitsToBytes(bits));
  }

  function luminanceOf(sample) {
    return 0.2126 * sample.r + 0.7152 * sample.g + 0.0722 * sample.b;
  }

  function rgbDistance(a, b) {
    const dr = a.r - b.r;
    const dg = a.g - b.g;
    const db = a.b - b.b;
    return Math.sqrt(dr * dr + dg * dg + db * db);
  }

  function clamp01(value) {
    if (!Number.isFinite(value)) return 0;
    return Math.max(0, Math.min(1, value));
  }

  function median(values) {
    if (!values.length) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }

  function medianRgb(samples) {
    return {
      r: median(samples.map(sample => sample.r)),
      g: median(samples.map(sample => sample.g)),
      b: median(samples.map(sample => sample.b))
    };
  }

  function normalizeCellSample(sample) {
    if (Array.isArray(sample) || ArrayBuffer.isView(sample)) {
      return { r: sample[0] || 0, g: sample[1] || 0, b: sample[2] || 0 };
    }
    return { r: sample.r || 0, g: sample.g || 0, b: sample.b || 0 };
  }

  function finderReferences(samples) {
    const dark = [];
    const light = [];
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        const expected = expectedFinderValue(row, col);
        if (expected === null) continue;
        (expected ? dark : light).push(samples[row][col]);
      }
    }
    if (!dark.length || !light.length) throw new Error("Finder references unavailable");
    const darkRgb = medianRgb(dark);
    const lightRgb = medianRgb(light);
    return {
      dark: { ...darkRgb, luminance: luminanceOf(darkRgb) },
      light: { ...lightRgb, luminance: luminanceOf(lightRgb) }
    };
  }

  function inkScore(sample, references) {
    const luminanceSpan = Math.max(1, references.light.luminance - references.dark.luminance);
    const luminanceScore = clamp01((references.light.luminance - luminanceOf(sample)) / luminanceSpan);
    const lightDistance = rgbDistance(sample, references.light);
    const darkDistance = rgbDistance(sample, references.dark);
    const distanceScore = lightDistance + darkDistance > 0 ? lightDistance / (lightDistance + darkDistance) : luminanceScore;
    const saturationScore = (Math.max(sample.r, sample.g, sample.b) - Math.min(sample.r, sample.g, sample.b)) / 255;
    return clamp01(0.6 * luminanceScore + 0.25 * distanceScore + 0.15 * saturationScore);
  }

  function otsuThreshold(scores) {
    if (!scores.length) return null;
    const bins = 64;
    const histogram = Array(bins).fill(0);
    for (const score of scores) histogram[Math.max(0, Math.min(bins - 1, Math.floor(clamp01(score) * (bins - 1))))]++;
    let total = 0;
    let weightedTotal = 0;
    for (let i = 0; i < bins; i++) {
      total += histogram[i];
      weightedTotal += i * histogram[i];
    }
    let backgroundWeight = 0;
    let backgroundSum = 0;
    let bestVariance = -1;
    let bestIndex = Math.floor(bins / 2);
    for (let i = 0; i < bins; i++) {
      backgroundWeight += histogram[i];
      if (!backgroundWeight) continue;
      const foregroundWeight = total - backgroundWeight;
      if (!foregroundWeight) break;
      backgroundSum += i * histogram[i];
      const backgroundMean = backgroundSum / backgroundWeight;
      const foregroundMean = (weightedTotal - backgroundSum) / foregroundWeight;
      const variance = backgroundWeight * foregroundWeight * (backgroundMean - foregroundMean) ** 2;
      if (variance > bestVariance) {
        bestVariance = variance;
        bestIndex = i;
      }
    }
    return (bestIndex + 0.5) / bins;
  }

  function thresholdFromScores(scores) {
    const finderDarkScores = [];
    const finderLightScores = [];
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        const expected = expectedFinderValue(row, col);
        if (expected === null) continue;
        (expected ? finderDarkScores : finderLightScores).push(scores[row][col]);
      }
    }
    const lightAnchor = median(finderLightScores);
    const darkAnchor = median(finderDarkScores);
    const anchorThreshold = (lightAnchor + darkAnchor) / 2;
    const dataScores = POSITIONS.map(([row, col]) => scores[row][col]);
    const adaptiveThreshold = otsuThreshold(dataScores);
    if (adaptiveThreshold === null) return anchorThreshold;
    const lower = Math.min(lightAnchor, darkAnchor) + 0.03;
    const upper = Math.max(lightAnchor, darkAnchor) - 0.03;
    if (upper <= lower) return anchorThreshold;
    return Math.max(lower, Math.min(upper, adaptiveThreshold));
  }

  function cellSamplesToMatrix(cellSamples) {
    const samples = cellSamples.map(row => row.map(normalizeCellSample));
    const references = finderReferences(samples);
    const scores = samples.map(row => row.map(sample => inkScore(sample, references)));
    const threshold = thresholdFromScores(scores);
    return scores.map(row => row.map(score => score >= threshold ? 1 : 0));
  }

  function encodeOpticalFrames(payload) {
    const encoded = b64urlFromBytes(utf8Bytes(JSON.stringify(payload)));
    const bytes = utf8Bytes(encoded);
    const count = Math.max(1, Math.ceil(bytes.length / MAX_DATA_BYTES));
    return Array.from({ length: count }, (_, index) => {
      const data = bytes.slice(index * MAX_DATA_BYTES, (index + 1) * MAX_DATA_BYTES);
      return { index, count, data, matrix: matrixFromFrame(index, count, data) };
    });
  }

  function decodeOpticalFrames(frameMap) {
    const frames = [...frameMap.values()].sort((a, b) => a.index - b.index);
    if (!frames.length) throw new Error("No frames captured");
    const count = frames[0].count;
    if (frames.length !== count) throw new Error(`Need ${count} frames, have ${frames.length}`);
    const total = frames.reduce((sum, frame) => sum + frame.data.length, 0);
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (let index = 0; index < frames.length; index++) {
      const frame = frames[index];
      if (frame.index !== index || frame.count !== count) throw new Error("Frame sequence mismatch");
      bytes.set(frame.data, offset);
      offset += frame.data.length;
    }
    return JSON.parse(utf8Text(bytesFromB64url(utf8Text(bytes))));
  }

  function drawMatrix(canvas, matrix, options = {}) {
    const ctx = canvas.getContext("2d");
    const size = Math.min(canvas.width, canvas.height);
    const cell = size / GRID_SIZE;
    ctx.fillStyle = options.background || "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate((canvas.width - size) / 2, (canvas.height - size) / 2);
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        const bit = matrix[row][col];
        const hue = (row * 17 + col * 23 + (bit ? 145 : 0)) % 360;
        ctx.fillStyle = bit ? `hsl(${hue} 82% 39%)` : "#f8fbff";
        if (isFinderCell(row, col)) ctx.fillStyle = bit ? "#050816" : "#ffffff";
        ctx.fillRect(col * cell, row * cell, Math.ceil(cell), Math.ceil(cell));
      }
    }
    ctx.restore();
  }

  function sampleCanvasToMatrix(canvas) {
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    const size = Math.min(canvas.width, canvas.height);
    const startX = (canvas.width - size) / 2;
    const startY = (canvas.height - size) / 2;
    const cell = size / GRID_SIZE;
    const samples = Array.from({ length: GRID_SIZE }, () => Array(GRID_SIZE).fill(null));
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        const x = Math.floor(startX + (col + 0.5) * cell);
        const y = Math.floor(startY + (row + 0.5) * cell);
        const [r, g, b] = ctx.getImageData(x, y, 1, 1).data;
        samples[row][col] = { r, g, b };
      }
    }
    return cellSamplesToMatrix(samples);
  }

  function senderPayload() {
    return {
      schema: "uvip_qsom_camera_mcp_envelope.v1",
      protocol: "UVIP-QSOM-CAMERA-MCP",
      protocol_version: "0.2.0",
      created_at: new Date().toISOString(),
      session_id: `cam-${crypto.randomUUID()}`,
      message_id: `msg-${crypto.randomUUID()}`,
      sender_id: "browser.sender.visual",
      receiver_id: "browser.receiver.visual",
      method: "tools/list",
      params: {
        transport: "camera-grade-optical-alpha",
        safety: "no secrets; receiver must authorize decoded method",
        frame_grid: `${GRID_SIZE}x${GRID_SIZE}`
      },
      transport_boundary: "Screen-to-camera visual transport is untrusted input until decoded, hash-checked, and authorized."
    };
  }

  return {
    GRID_SIZE,
    cellSamplesToMatrix,
    decodeOpticalFrames,
    drawMatrix,
    encodeOpticalFrames,
    frameFromMatrix,
    sampleCanvasToMatrix,
    senderPayload
  };
})();

if (typeof module !== "undefined") module.exports = QSOM;
