#!/usr/bin/env python3
"""Report which skills named in the Office OS routing guide are installed.

Advisory only: Office OS works without optional skills. With --check-removed
the exit code is non-zero if a reference file still names a skill the package
has removed (see manifest.json "removed_skills").
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
REFS = SOURCE.parent / 'references'
MANIFEST = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
NAME = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$|^[a-z]+$')
TABLE_SECTIONS = ('## Default engineering stack', '## Specialist routing')


def referenced():
    names = set()
    active = False
    for line in (REFS / 'routing.md').read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            active = line.strip() in TABLE_SECTIONS
        if active and line.startswith('|'):
            for token in re.findall(r'`([^`]+)`', line):
                if NAME.match(token):
                    names.add(token)
    return names


def installed(cfg):
    names = set()
    roots = [cfg / 'skills', cfg / 'plugins']
    for root in roots:
        if not root.is_dir():
            continue
        for skill_md in root.rglob('SKILL.md'):
            names.add(skill_md.parent.name)
            match = re.search(r'^name:\s*(\S+)', skill_md.read_text(encoding='utf-8', errors='replace'), re.M)
            if match:
                names.add(match.group(1).split(':')[-1])
    return names


def removed_mentions():
    hits = []
    removed = set(MANIFEST.get('removed_skills', []))
    for path in sorted(REFS.glob('*.md')):
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            for token in re.findall(r'`([^`]+)`', line):
                if token in removed:
                    hits.append(f'{path.name}:{number}: `{token}` was removed from the package')
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config-dir', default=os.environ.get('CLAUDE_CONFIG_DIR') or str(Path.home() / '.claude'))
    ap.add_argument('--check-removed', action='store_true', help='fail if references name a removed skill')
    args = ap.parse_args()
    hits = removed_mentions()
    for hit in hits:
        print('STALE ', hit)
    if args.check_removed:
        return 1 if hits else 0
    have = installed(Path(args.config_dir))
    want = referenced()
    present = sorted(want & have)
    missing = sorted(want - have)
    print('Installed (' + str(len(present)) + '):', ', '.join(present) or 'none')
    print('Not installed (' + str(len(missing)) + '):', ', '.join(missing) or 'none')
    print('Built-in skills (for example code-review) are not detected from disk.')
    print('Missing skills are optional: do the underlying work directly with project tools.')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
