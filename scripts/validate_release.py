#!/usr/bin/env python3
"""Offline release invariants and the decision-focused synthetic query tests."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/bmtc-data'


def main():
    version = (ROOT / 'VERSION').read_text().strip()
    assert re.fullmatch(r'\d+\.\d+\.\d+', version)
    for relative in ['plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json']:
        manifest = json.loads((PLUGIN / relative).read_text())
        assert manifest['name'] == 'bmtc-data'
        assert manifest['version'] == version
        assert manifest['license'] == 'MIT'
        assert manifest['repository'] == 'https://github.com/Kargnin/bmtc-agent-plugin'
        assert 'mcpServers' not in manifest
    portable = json.loads((PLUGIN / 'plugin.json').read_text())
    codex = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text())
    assert portable['extensions']['com.openai']['interface'] == codex['interface']
    assert len(codex['interface']['displayName']) <= 30
    assert len(codex['interface']['shortDescription']) <= 30
    for key in ['composerIcon', 'logo', 'logoDark']:
        asset = PLUGIN / codex['interface'][key]
        assert asset.is_file() and asset.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    for relative in ['.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json']:
        market = json.loads((ROOT / relative).read_text())
        assert market['name'] == 'bmtc-agent-plugins'
        assert market['plugins'][0]['name'] == 'bmtc-data'
    assert len((PLUGIN / 'README.md').read_text().split()) >= 40
    for path in PLUGIN.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts: continue
        assert not path.is_symlink(), str(path)
        assert path.stat().st_size < 256 * 1024, str(path)
        assert path.suffix not in ['.sqlite3', '.db', '.zip', '.pdf'], str(path)
        if path.suffix in ['.md', '.json', '.py']:
            text = path.read_text()
            assert '/Users/' not in text, str(path)
            assert '[TODO:' not in text, str(path)
            assert not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,})', text), str(path)
    subprocess.run([sys.executable, '-B', str(PLUGIN/'skills/bmtc-data/scripts/test_queries.py')], check=True)
    print('Release metadata, package boundaries and synthetic decision checks passed.')


if __name__ == '__main__':
    main()
