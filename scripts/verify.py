"""Check installed asset hashes and Codex v2 dimensions; Python 3, no dependencies."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
assert len(catalog) == len({pet['id'] for pet in catalog}), 'Duplicate pet ID'
for pet in catalog:
    folder = (root / pet['directory']).resolve()
    assert folder.parent == (root / 'pets').resolve(), 'Invalid pet path'
    manifest = json.loads((folder / 'pet.json').read_text(encoding='utf-8-sig'))
    assert manifest['id'] == pet['id']
    assert manifest['spriteVersionNumber'] == 2
    assert manifest['spritesheetPath'] == 'spritesheet.webp'
    for filename, expected in pet['sha256'].items():
        assert filename in ('pet.json', 'spritesheet.webp'), 'Unexpected asset'
        assert hashlib.sha256((folder / filename).read_bytes()).hexdigest() == expected, f'Hash mismatch: {pet["id"]}/{filename}'
    data = (folder / 'spritesheet.webp').read_bytes()
    assert data[:4] == b'RIFF' and data[8:12] == b'WEBP', 'Invalid WebP'
    position = 12
    dimensions = None
    while position + 8 <= len(data):
        kind = data[position:position+4]
        size = int.from_bytes(data[position+4:position+8], 'little')
        chunk = data[position+8:position+8+size]
        if kind == b'VP8X':
            dimensions = (1+int.from_bytes(chunk[4:7], 'little'), 1+int.from_bytes(chunk[7:10], 'little'))
        elif kind == b'VP8L' and dimensions is None:
            assert chunk[0] == 0x2f
            bits = int.from_bytes(chunk[1:5], 'little')
            dimensions = ((bits & 0x3fff)+1, ((bits >> 14) & 0x3fff)+1)
        position += 8 + size + (size % 2)
    assert dimensions == (1536, 2288), f'Invalid atlas size: {pet["id"]}'
print(f'PASS: {len(catalog)} pets; asset hashes, manifests and v2 dimensions verified.')
