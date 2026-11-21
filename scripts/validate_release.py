#!/usr/bin/env python3
"""Offline package boundaries and decision-focused synthetic tests."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/bmtc-data'


def main():
    version = (ROOT/'VERSION').read_text().strip()
    assert re.fullmatch(r'\d+\.\d+\.\d+', version)
    text = (SKILL/'SKILL.md').read_text()
    assert text.startswith('---\nname: bmtc-data\n')
    assert '\ndescription: ' in text.split('---', 2)[1]
    assert (SKILL/'LICENSE').is_file()
    for path in SKILL.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts: continue
        assert not path.is_symlink(), str(path)
        assert path.stat().st_size < 256*1024, str(path)
        assert path.suffix not in ['.sqlite3', '.db', '.zip', '.pdf'], str(path)
        if path.suffix in ['.md', '.json', '.py']:
            content=path.read_text()
            assert '/Users/' not in content, str(path)
            assert '[TODO:' not in content, str(path)
            assert not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,})',content), str(path)
    subprocess.run([sys.executable,'-B',str(SKILL/'scripts/test_queries.py')],check=True)
    print('Skill package boundaries and synthetic decision checks passed.')


if __name__=='__main__': main()
