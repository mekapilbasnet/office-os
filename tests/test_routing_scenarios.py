"""Consistency check for Office OS routing guidance.

The routing is prose that a model follows, so this cannot grade a model's choice.
It checks that every scenario in routing_scenarios.json points at a mode, risk
level, route, and skill that the guides actually define, and that no guide names
a skill the package has removed.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICE = ROOT / 'office-os'
SCENARIOS = json.loads((Path(__file__).parent / 'routing_scenarios.json').read_text(encoding='utf-8'))
SKILL = (OFFICE / 'SKILL.md').read_text(encoding='utf-8')
ROUTING = (OFFICE / 'references/routing.md').read_text(encoding='utf-8')


def sections(text, prefix):
    """Map heading title -> body for every heading that starts with `prefix` (for example '### ').

    Any other heading line ends the current section.
    """
    found, title, body = {}, None, []
    for line in text.splitlines() + ['# end']:
        if line.startswith('#'):
            if title is not None:
                found[title] = '\n'.join(body)
            title, body = (line[len(prefix):].strip() if line.startswith(prefix) else None), []
        elif title is not None:
            body.append(line)
    return found


def table_rows(text, first_header):
    """Rows (list of cell strings) of the markdown table whose header row starts with `first_header`."""
    rows, inside = [], False
    for line in text.splitlines():
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if cells[0] == first_header:
                inside = True
            elif inside and not set(cells[0]) <= set('-: '):
                rows.append(cells)
        else:
            inside = False
    return rows


MODES = {row[0] for row in table_rows(SKILL, 'Mode')}
RISKS = {row[0]: row for row in table_rows(ROUTING, 'Level')}
ROUTES = sections(ROUTING, '### ')
SPECIALISTS = {row[0]: row[1] for row in table_rows(ROUTING, 'Task signal')}


class RoutingScenarios(unittest.TestCase):
    def test_parsers_found_the_guide_structure(self):
        self.assertTrue({'Direct', 'Standard', 'Full lifecycle', 'Incident'} <= MODES, MODES)
        self.assertEqual(set(RISKS), {'Low', 'Moderate', 'High', 'Critical'})
        self.assertTrue(all(body.strip() for body in ROUTES.values()))
        self.assertIn('Bug', ROUTES)

    def test_modes_risks_routes_and_skills_are_defined(self):
        for case in SCENARIOS:
            with self.subTest(request=case['request']):
                self.assertIn(case['mode'], MODES)
                self.assertIn(case['risk'], RISKS)
                self.assertIn(case['route'], ROUTES)
                # Each expected skill must be named by the scenario's own route, not merely somewhere in the guide.
                for skill in case.get('skills', []):
                    self.assertIn('`' + skill + '`', ROUTES[case['route']], skill + ' missing from route ' + case['route'])
                # Specialist skills come from the matching row of the specialist routing table.
                for skill in case.get('specialists', []):
                    self.assertIn(case['signal'], SPECIALISTS)
                    self.assertIn('`' + skill + '`', SPECIALISTS[case['signal']])

    def test_no_reference_names_a_removed_skill(self):
        r = subprocess.run([sys.executable, str(OFFICE / 'routing-tools/skills_check.py'), '--check-removed'],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_new_files_are_owned_and_linked(self):
        manifest = json.loads((OFFICE / 'routing-tools/manifest.json').read_text(encoding='utf-8'))
        for rel in ('references/templates.md', 'routing-tools/subagents/reviewer.md', 'routing-tools/skills_check.py'):
            self.assertIn(rel, manifest['owned_office_files'])
            self.assertTrue((OFFICE / rel).is_file())
        self.assertIn('references/templates.md', SKILL)
        self.assertEqual(manifest['agents']['reviewer'], 'sonnet')


if __name__ == '__main__':
    unittest.main()
