#!/usr/bin/env python3
"""Create README derivatives; never rewrite screenshots or their manifest."""
import hashlib
import json
from pathlib import Path

from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / 'previews'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = PREVIEWS / 'thumbs'
    target.mkdir(exist_ok=True)
    records = []
    for source in sorted((PREVIEWS / 'actual').rglob('*.png')):
        relative = source.relative_to(PREVIEWS / 'actual')
        output = (target / relative).with_suffix('.png')
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as original:
            size = [original.width, original.height]
            thumbnail = original.convert('RGB')
            thumbnail.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
            thumbnail.save(output, optimize=True)
            records.append({
                'source': source.relative_to(PREVIEWS).as_posix(), 'source_sha256': digest(source),
                'source_dimensions': size, 'thumbnail': output.relative_to(PREVIEWS).as_posix(),
                'thumbnail_sha256': digest(output), 'thumbnail_dimensions': list(thumbnail.size),
            })
    manifest = {'source_manifest': 'manifest.json', 'source_manifest_sha256': digest(PREVIEWS / 'manifest.json'),
                'purpose': 'README thumbnails of the unchanged v1.1 reference captures; not v1.2 acceptance',
                'generator': 'scripts/generate-thumbnails.py', 'pillow_version': pillow_version,
                'resize': 'LANCZOS, fit 1000x1000, no upscale, RGB PNG', 'images': records}
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
