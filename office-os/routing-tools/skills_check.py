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


def bundled_subagents():
    """Names of subagents the installer provides; they are agents, not skills."""
    try:
        return {p.stem for p in (SOURCE / 'subagents').glob('*.md')}
    except OSError:
        return set()


def installed(cfg):
    names = set()
    roots = [cfg / 'skills', cfg / 'plugins']
    for root in roots:
        if not root.is_dir():
            continue
        for skill_md in root.rglob('SKILL.md'):
            names.add(skill_md.parent.name)
            name = frontmatter_name(skill_md.read_text(encoding='utf-8', errors='replace'))
            if name:
                names.add(name.split(':')[-1])
    return names


def load_manifest():
    path = SOURCE / 'manifest.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise RuntimeError(f'Cannot load {path}: {error}')
    if not isinstance(data, dict):
        raise RuntimeError(f'Cannot load {path}: expected a JSON object')
    return data


def frontmatter_name(text):
    """Return the `name:` value from the leading YAML frontmatter block only."""
    lines = text.lstrip('\ufeff').splitlines()
    if not lines or lines[0].strip() != '---':
        return None
    for line in lines[1:]:
        if line.strip() == '---':
            break
        match = re.match(r'name:\s*["\']?([^\s"\']+)', line)
        if match:
            return match.group(1)
    return None


def removed_mentions():
    hits = []
    removed = set(load_manifest().get('removed_skills', []))
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
    try:
        hits = removed_mentions()
    except RuntimeError as error:
        print('ERROR:', error, file=sys.stderr)
        return 1
    for hit in hits:
        print('STALE ', hit)
    if args.check_removed:
        return 1 if hits else 0
    have = installed(Path(args.config_dir))
    want = referenced() - bundled_subagents()
    present = sorted(want & have)
    missing = sorted(want - have)
    print('Installed (' + str(len(present)) + '):', ', '.join(present) or 'none')
    print('Not installed (' + str(len(missing)) + '):', ', '.join(missing) or 'none')
    print('Built-in skills (for example code-review) are not detected from disk.')
    print('Missing skills are optional: do the underlying work directly with project tools.')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
