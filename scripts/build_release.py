#!/usr/bin/env python3
"""Build deterministic native-platform bundles from the canonical plugin folder."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/bmtc-data'


def build(output, excluded):
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PLUGIN.rglob('*')):
            relative = path.relative_to(PLUGIN)
            if not path.is_file() or '__pycache__' in relative.parts or path.suffix == '.pyc':
                continue
            if any(relative == Path(x) or str(relative).startswith(x + '/') for x in excluded):
                continue
            info = zipfile.ZipInfo('bmtc-data/' + relative.as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main():
    version = (ROOT / 'VERSION').read_text().strip()
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    packages = {
        'openai': ['.claude-plugin'],
        'claude': ['.codex-plugin', 'plugin.json'],
    }
    sums = []
    for platform, excluded in packages.items():
        target = dist / f'bmtc-data-{platform}-{version}.zip'
        build(target, excluded)
        sums.append(hashlib.sha256(target.read_bytes()).hexdigest() + '  ' + target.name)
        print(target.relative_to(ROOT), target.stat().st_size, 'bytes')
    (dist / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')


if __name__ == '__main__':
    main()
