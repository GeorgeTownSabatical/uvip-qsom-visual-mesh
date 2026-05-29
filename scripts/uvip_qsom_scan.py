#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uvip_qsom_visual_mesh.receiver import scan_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan UVIP/QSO visual MCP metadata.")
    parser.add_argument("source")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = scan_path(Path(args.source))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    if args.strict and not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

