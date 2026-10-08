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


class RoutingScenarios(unittest.TestCase):
    def test_modes_risks_routes_and_skills_are_defined(self):
        for case in SCENARIOS:
            with self.subTest(request=case['request']):
                self.assertIn('| ' + case['mode'] + ' |', SKILL)
                self.assertIn('| ' + case['risk'] + ' |', ROUTING)
                self.assertIn('### ' + case['route'], ROUTING)
                for skill in case.get('skills', []):
                    self.assertIn('`' + skill + '`', ROUTING)

    def test_no_reference_names_a_removed_skill(self):
        r = subprocess.run([sys.executable, str(OFFICE / 'routing-tools/skills_check.py'), '--check-removed'],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_new_files_are_owned_and_linked(self):
        manifest = json.loads((OFFICE / 'routing-tools/manifest.json').read_text(encoding='utf-8'))
        for rel in ('references/templates.md', 'routing-tools/agents/reviewer.md', 'routing-tools/skills_check.py'):
            self.assertIn(rel, manifest['owned_office_files'])
            self.assertTrue((OFFICE / rel).is_file())
        self.assertIn('references/templates.md', SKILL)
        self.assertEqual(manifest['agents']['reviewer'], 'sonnet')


if __name__ == '__main__':
    unittest.main()
