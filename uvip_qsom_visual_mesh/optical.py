from __future__ import annotations

import math
import struct
import zlib
from dataclasses import dataclass

from .codec import b64url_decode, b64url_encode

MAGIC = b"QSOM"
VERSION = 1
GRID_SIZE = 41
FINDER_SIZE = 7
HEADER_STRUCT = struct.Struct(">4sBHHHI")
HEADER_SIZE = HEADER_STRUCT.size
MAX_DATA_BYTES = 128


@dataclass(frozen=True)
class OpticalFrame:
    frame_index: int
    frame_count: int
    data: bytes
    matrix: list[list[int]]
    checksum: int


@dataclass(frozen=True)
class MatrixScore:
    dimensions_ok: bool
    finder_mismatches: int
    finder_cells: int
    finder_confidence: float

    @property
    def acceptable(self) -> bool:
        return self.dimensions_ok and self.finder_confidence >= 0.88


def is_finder_cell(row: int, col: int, grid_size: int = GRID_SIZE, finder_size: int = FINDER_SIZE) -> bool:
    in_left = col < finder_size
    in_right = col >= grid_size - finder_size
    in_top = row < finder_size
    in_bottom = row >= grid_size - finder_size
    return (in_top and in_left) or (in_top and in_right) or (in_bottom and in_left)


def data_positions(grid_size: int = GRID_SIZE) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(grid_size)
        for col in range(grid_size)
        if not is_finder_cell(row, col, grid_size)
    ]


def bytes_to_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for index in range(0, len(bits), 8):
        value = 0
        for bit in bits[index : index + 8]:
            value = (value << 1) | (bit & 1)
        if len(bits[index : index + 8]) == 8:
            out.append(value)
    return bytes(out)


def finder_value(local_row: int, local_col: int) -> int:
    if local_row in {0, 6} or local_col in {0, 6}:
        return 1
    if local_row in {1, 5} or local_col in {1, 5}:
        return 0
    return 1


def draw_finders(matrix: list[list[int]]) -> None:
    starts = [(0, 0), (0, GRID_SIZE - FINDER_SIZE), (GRID_SIZE - FINDER_SIZE, 0)]
    for start_row, start_col in starts:
        for row in range(FINDER_SIZE):
            for col in range(FINDER_SIZE):
                matrix[start_row + row][start_col + col] = finder_value(row, col)


def expected_finder_matrix(grid_size: int = GRID_SIZE) -> list[list[int | None]]:
    expected: list[list[int | None]] = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    starts = [(0, 0), (0, grid_size - FINDER_SIZE), (grid_size - FINDER_SIZE, 0)]
    for start_row, start_col in starts:
        for row in range(FINDER_SIZE):
            for col in range(FINDER_SIZE):
                expected[start_row + row][start_col + col] = finder_value(row, col)
    return expected


def score_matrix(matrix: list[list[int]]) -> MatrixScore:
    dimensions_ok = len(matrix) == GRID_SIZE and all(len(row) == GRID_SIZE for row in matrix)
    if not dimensions_ok:
        return MatrixScore(False, finder_mismatches=GRID_SIZE * GRID_SIZE, finder_cells=GRID_SIZE * GRID_SIZE, finder_confidence=0.0)
    expected = expected_finder_matrix()
    finder_cells = 0
    mismatches = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            expected_value = expected[row][col]
            if expected_value is None:
                continue
            finder_cells += 1
            if int(bool(matrix[row][col])) != expected_value:
                mismatches += 1
    confidence = 1.0 - (mismatches / finder_cells if finder_cells else 1.0)
    return MatrixScore(True, finder_mismatches=mismatches, finder_cells=finder_cells, finder_confidence=confidence)


def majority_matrix(matrices: list[list[list[int]]]) -> list[list[int]]:
    if not matrices:
        raise ValueError("no matrices supplied")
    if any(len(matrix) != GRID_SIZE or any(len(row) != GRID_SIZE for row in matrix) for matrix in matrices):
        raise ValueError("matrix has wrong dimensions")
    threshold = len(matrices) / 2
    result: list[list[int]] = []
    for row in range(GRID_SIZE):
        out_row: list[int] = []
        for col in range(GRID_SIZE):
            out_row.append(1 if sum(int(bool(matrix[row][col])) for matrix in matrices) > threshold else 0)
        result.append(out_row)
    return result


def encode_frame_bytes(frame_index: int, frame_count: int, data: bytes) -> bytes:
    if len(data) > MAX_DATA_BYTES:
        raise ValueError(f"frame data exceeds {MAX_DATA_BYTES} bytes")
    checksum = zlib.crc32(data) & 0xFFFFFFFF
    return HEADER_STRUCT.pack(MAGIC, VERSION, frame_index, frame_count, len(data), checksum) + data


def decode_frame_bytes(raw: bytes) -> tuple[int, int, bytes, int]:
    if len(raw) < HEADER_SIZE:
        raise ValueError("frame is shorter than header")
    magic, version, frame_index, frame_count, length, checksum = HEADER_STRUCT.unpack(raw[:HEADER_SIZE])
    if magic != MAGIC:
        raise ValueError("bad frame magic")
    if version != VERSION:
        raise ValueError("unsupported frame version")
    data = raw[HEADER_SIZE : HEADER_SIZE + length]
    if len(data) != length:
        raise ValueError("frame payload truncated")
    if (zlib.crc32(data) & 0xFFFFFFFF) != checksum:
        raise ValueError("frame checksum mismatch")
    return frame_index, frame_count, data, checksum


def frame_to_matrix(frame_index: int, frame_count: int, data: bytes) -> OpticalFrame:
    raw = encode_frame_bytes(frame_index, frame_count, data)
    bits = bytes_to_bits(raw)
    positions = data_positions()
    if len(bits) > len(positions):
        raise ValueError("frame does not fit in optical grid")
    matrix = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    draw_finders(matrix)
    for bit, (row, col) in zip(bits, positions):
        matrix[row][col] = bit
    checksum = zlib.crc32(data) & 0xFFFFFFFF
    return OpticalFrame(frame_index=frame_index, frame_count=frame_count, data=data, matrix=matrix, checksum=checksum)


def matrix_to_frame(matrix: list[list[int]]) -> OpticalFrame:
    if len(matrix) != GRID_SIZE or any(len(row) != GRID_SIZE for row in matrix):
        raise ValueError("matrix has wrong dimensions")
    score = score_matrix(matrix)
    if not score.acceptable:
        raise ValueError(f"finder confidence too low: {score.finder_confidence:.3f}")
    bits = [matrix[row][col] for row, col in data_positions()]
    raw = bits_to_bytes(bits)
    frame_index, frame_count, data, checksum = decode_frame_bytes(raw)
    return OpticalFrame(frame_index=frame_index, frame_count=frame_count, data=data, matrix=matrix, checksum=checksum)


def encode_optical_frames(encoded_payload: str, *, data_bytes_per_frame: int = MAX_DATA_BYTES) -> list[OpticalFrame]:
    data = encoded_payload.encode("ascii")
    frame_count = max(1, math.ceil(len(data) / data_bytes_per_frame))
    return [
        frame_to_matrix(index, frame_count, data[index * data_bytes_per_frame : (index + 1) * data_bytes_per_frame])
        for index in range(frame_count)
    ]


def decode_optical_frames(frames: list[OpticalFrame]) -> str:
    if not frames:
        raise ValueError("no frames supplied")
    ordered = sorted(frames, key=lambda frame: frame.frame_index)
    expected = ordered[0].frame_count
    if len(ordered) != expected:
        raise ValueError(f"expected {expected} frames, received {len(ordered)}")
    for index, frame in enumerate(ordered):
        if frame.frame_index != index:
            raise ValueError("frame sequence is incomplete")
        if frame.frame_count != expected:
            raise ValueError("frame count mismatch")
    return b"".join(frame.data for frame in ordered).decode("ascii")


def interpret_repeated_matrices(matrices: list[list[list[int]]]) -> OpticalFrame:
    """Decode repeated captures of the same optical frame using per-cell majority vote."""
    return matrix_to_frame(majority_matrix(matrices))


def roundtrip_payload_bytes(data: bytes) -> bytes:
    encoded = b64url_encode(data)
    frames = encode_optical_frames(encoded)
    decoded = decode_optical_frames([matrix_to_frame(frame.matrix) for frame in frames])
    return b64url_decode(decoded)
