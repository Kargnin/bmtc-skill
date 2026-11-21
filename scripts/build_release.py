#!/usr/bin/env python3
"""Build a deterministic portable skill ZIP and checksum."""
import hashlib
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/bmtc-data'


def main():
    version=(ROOT/'VERSION').read_text().strip()
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/f'bmtc-data-skill-{version}.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(SKILL.rglob('*')):
            relative=path.relative_to(SKILL)
            if not path.is_file() or '__pycache__' in relative.parts or path.suffix=='.pyc': continue
            info=zipfile.ZipInfo('bmtc-data/'+relative.as_posix(),(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,path.read_bytes())
    (dist/'SHA256SUMS').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print(target.relative_to(ROOT),target.stat().st_size,'bytes')


if __name__=='__main__': main()
