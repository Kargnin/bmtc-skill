#!/usr/bin/env python3
"""Keep host manifests and marketplace metadata on one explicit release version."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/bmtc-data'


def main():
    version = sys.argv[1]
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise SystemExit('Use a stable X.Y.Z version.')
    for relative in ['plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json']:
        path = PLUGIN / relative
        data = json.loads(path.read_text())
        data['version'] = version
        path.write_text(json.dumps(data, indent=2) + '\n')
    path = ROOT / '.claude-plugin/marketplace.json'
    data = json.loads(path.read_text())
    data['plugins'][0]['version'] = version
    path.write_text(json.dumps(data, indent=2) + '\n')
    (ROOT / 'VERSION').write_text(version + '\n')
    print(version)


if __name__ == '__main__':
    main()
