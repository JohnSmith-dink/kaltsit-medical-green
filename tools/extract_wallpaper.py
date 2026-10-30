#!/usr/bin/env python3
"""Reproduce the unmodified JPEG from the existing local VBG; no dependencies."""
import argparse
import hashlib
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("vbg", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
with args.vbg.open("rb") as source:
    source.seek(235975272)
    frame = source.read(331729)
digest = hashlib.sha256(frame).hexdigest()
if digest != "1427f0b9f220686a1c1b0bb654c1145302a54c9ba0a44d90dcdcbf5317ae2e8b":
    parser.error("VBG does not match the recorded frame; refusing to extract different data")
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(frame)
print(f"{digest}  {args.output}")
