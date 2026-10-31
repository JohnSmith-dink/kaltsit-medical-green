#!/usr/bin/env python3
"""Make a reproducible source archive and SHA256SUMS without private state."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
output = (args.output_dir or root.parent / "dist").resolve()
output.mkdir(parents=True, exist_ok=True)
prefix = "kaltsit-medical-green-1.1.0-rc.1"
archive = output / (prefix + ".tar.gz")
excluded = {".git", "__pycache__", ".direnv", "dist", "build", "result"}
files = []
for path in sorted(root.rglob("*")):
    rel = path.relative_to(root)
    if any(part in excluded or part.startswith("result-") for part in rel.parts):
        continue
    if path.name.endswith((".pyc", ".pyo")) or path.name.startswith(".env") or path.name == "active.json":
        continue
    if path.is_symlink() or path.is_file():
        files.append(path)
with archive.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as gz:
    with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for path in files:
            name = str(Path(prefix) / path.relative_to(root))
            info = tar.gettarinfo(str(path), arcname=name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            info.pax_headers = {}
            info.mode = 0o777 if info.issym() else 0o644
            if info.issym():
                if Path(info.linkname).is_absolute() or ".." in Path(info.linkname).parts:
                    raise SystemExit(f"Unsafe archive link: {name}")
                tar.addfile(info)
            else:
                tar.addfile(info, io.BytesIO(path.read_bytes()))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
print(f"{digest}  {archive}")
print(f"{len(files)} files, {archive.stat().st_size} bytes")
