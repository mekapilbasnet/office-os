import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manager', ROOT / 'office-os/routing-tools/routing_manager.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = Path(self.tmp.name) / '.claude'

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'office-os/routing-tools/routing_manager.py'), *args,
                               '--config-dir', str(self.cfg)], capture_output=True, text=True)

    def test_read_only_preview(self):
        result = self.cli('plan')
        self.assertEqual(result.returncode, 0)
        self.assertIn('PREVIEW ONLY', result.stdout)
        self.assertFalse(self.cfg.exists())

    def test_install_verify_rollback_restores_exact_settings(self):
        self.cfg.mkdir()
        original = {'permissions': {'allow': ['Read']}, 'env': {'MY_VAR': 'keep'}}
        (self.cfg / 'settings.json').write_text(json.dumps(original))
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        self.assertEqual(self.cli('verify').returncode, 0)
        new = json.loads((self.cfg / 'settings.json').read_text())
        self.assertEqual(new['permissions'], original['permissions'])
        self.assertEqual(new['env'], original['env'])
        self.assertEqual(new['model'], 'sonnet')
        self.assertIn('office-os', new['statusLine']['command'])
        self.assertTrue((self.cfg / 'skills/office-os/SKILL.md').exists())
        self.assertEqual(self.cli('rollback', '--apply').returncode, 0)
        self.assertEqual(json.loads((self.cfg / 'settings.json').read_text()), original)
        self.assertFalse((self.cfg / 'agents/Explore.md').exists())

    def test_upgrade_exact_v3(self):
        for path in ('agents/Explore.md', 'agents/deep-reasoner.md', 'rules/model-routing.md'):
            dst = self.cfg / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes((ROOT / 'tests/fixtures/v3' / path).read_bytes())
        result = self.cli('install', '--apply')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('UPGRADE', result.stdout)
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual((self.cfg / 'rules/model-routing.md').read_bytes(), (ROOT / 'tests/fixtures/v3/rules/model-routing.md').read_bytes())

    def test_conflict_never_overwrites_without_explicit_replace(self):
        agent = self.cfg / 'agents/Explore.md'
        agent.parent.mkdir(parents=True)
        agent.write_text('custom agent!')
        result = self.cli('install', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(agent.read_text(), 'custom agent!')
        self.assertFalse((self.cfg / 'settings.json').exists())
        result = self.cli('install', '--apply', '--replace')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual(agent.read_text(), 'custom agent!')

    def test_reinstall_is_no_op(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        prior = (self.cfg / 'office-os-routing/state.json').read_bytes()
        result = self.cli('install', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ALREADY INSTALLED', result.stdout)
        self.assertEqual((self.cfg / 'office-os-routing/state.json').read_bytes(), prior)

    def test_preexisting_custom_settings_preserved(self):
        self.cfg.mkdir()
        base = {'model': 'opus', 'statusLine': {'type':'command','command':'echo existing'}, 'env': {'x':'y'}}
        (self.cfg / 'settings.json').write_text(json.dumps(base))
        result = self.cli('install', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((self.cfg / 'settings.json').read_text())
        self.assertEqual(data['model'], 'opus')
        self.assertEqual(data['statusLine'], base['statusLine'])
        self.assertIn('office-os', data['subagentStatusLine']['command'])
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual(json.loads((self.cfg / 'settings.json').read_text()), base)

    def test_force_subagent_model_causes_verify_failure(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        path = self.cfg / 'settings.json'
        data = json.loads(path.read_text())
        data['env'] = {'CLAUDE_CODE_SUBAGENT_MODEL_FORCE': '1'}
        path.write_text(json.dumps(data))
        result = self.cli('verify')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FAIL', result.stdout)

    def test_edited_file_protected_on_uninstall(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        agent = self.cfg / 'agents/Explore.md'
        agent.write_text(agent.read_text() + '\ncustomized\n')
        result = self.cli('uninstall', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('customized', agent.read_text())

    def test_installed_manager_works_without_original_sources(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        installed = self.cfg / 'skills/office-os/routing-tools/routing_manager.py'
        result = subprocess.run([sys.executable, str(installed), 'verify', '--config-dir', str(self.cfg)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('STATIC VERIFICATION: PASSED', result.stdout)

    def test_rollback_refuses_to_discard_later_edits(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        path = self.cfg / 'settings.json'
        settings = json.loads(path.read_text())
        settings['myLaterEdit'] = 'do not lose'
        path.write_text(json.dumps(settings))
        result = self.cli('rollback', '--apply')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(path.read_text())['myLaterEdit'], 'do not lose')

    def test_status_script_actual_model_and_subagent_json(self):
        script = ROOT / 'office-os/routing-tools/scripts/statusline.py'
        main = subprocess.run([sys.executable, str(script)], input=json.dumps({'model': {'display_name': 'Opus 5.5'}, 'workspace': {'current_dir': '/tmp/x'}, 'context_window': {'used_percentage': 38}}), capture_output=True, text=True)
        self.assertEqual(main.returncode, 0)
        self.assertIn('Model: Opus 5.5', main.stdout)
        sub = subprocess.run([sys.executable, str(ROOT / 'office-os/routing-tools/scripts/subagent_statusline.py')], input=json.dumps({'tasks':[{'id':'7','name':'Explore','status':'running','model':'claude-haiku-example','description':'Find files'}]}), capture_output=True, text=True)
        row = json.loads(sub.stdout)
        self.assertIn('claude-haiku-example', row['content'])
        self.assertEqual(row['id'], '7')


    def test_office_references_and_commands_present(self):
        self.assertEqual(self.cli('install', '--apply').returncode, 0)
        office=self.cfg / 'skills/office-os'
        text=(office/'SKILL.md').read_text()
        self.assertIn('references/model-routing.md', text)
        self.assertIn('references/governance.md', text)
        self.assertIn('## Model routing in Claude Code', text)
        self.assertIn('/office-os routing verify', (office/'references/command-surface.md').read_text())
        self.assertIn('## Model routing', (office/'references/routing.md').read_text())
        self.assertFalse((self.cfg/'skills/dynamic-routing/SKILL.md').exists())

    def test_clean_existing_office_os_can_upgrade(self):
        source=ROOT / 'tests/fixtures/office-original'
        for p in source.rglob('*'):
            if p.is_file():
                dest=self.cfg/'skills/office-os'/p.relative_to(source)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(p.read_bytes())
        installed=self.cli('install','--apply')
        self.assertEqual(installed.returncode,0, installed.stdout+installed.stderr)
        self.assertIn('UPGRADE',installed.stdout)
        self.assertEqual(self.cli('uninstall','--apply').returncode,0)
        for p in source.rglob('*'):
            if p.is_file():
                self.assertEqual((self.cfg/'skills/office-os'/p.relative_to(source)).read_bytes(),p.read_bytes())

    def test_custom_office_skill_protected_and_restorable(self):
        skill=self.cfg/'skills/office-os/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: office-os\n---\nUSER CUSTOM WORK')
        result=self.cli('install','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('USER CUSTOM WORK',skill.read_text())
        self.assertEqual(self.cli('install','--apply','--replace').returncode,0)
        self.assertEqual(self.cli('uninstall','--apply').returncode,0)
        self.assertIn('USER CUSTOM WORK',skill.read_text())

    def test_separate_v4_installer_must_be_removed_first(self):
        old=self.cfg/'dynamic-routing/state.json'
        old.parent.mkdir(parents=True)
        old.write_text('{}')
        result=self.cli('install','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.cfg/'skills/office-os/SKILL.md').exists())
        self.assertIn('Standalone Dynamic Routing v4',result.stdout)

    def test_failed_verify_missing_original_office_reference(self):
        self.assertEqual(self.cli('install','--apply').returncode,0)
        (self.cfg/'skills/office-os/references/governance.md').unlink()
        result=self.cli('verify')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Missing skills/office-os/references/governance.md',result.stdout)

    def test_auto_enabled_default_and_single_parent_skill(self):
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        self.assertTrue((self.cfg/'commands/dynamic-routing.md').is_file())
        self.assertTrue((self.cfg/'skills/office-os/SKILL.md').is_file())
        self.assertFalse((self.cfg/'skills/dynamic-routing/SKILL.md').exists())
        self.assertIn('ROUTING_STATE: ON', (self.cfg/'rules/model-routing.md').read_text())
        result=self.cli('status')
        self.assertEqual(result.returncode, 0)
        self.assertIn('ON (auto-activated)', result.stdout)

    def test_off_on_roundtrip_cleans_only_package_owned_model(self):
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        self.assertEqual(self.cli('off','--apply').returncode, 0)
        self.assertIn('ROUTING_STATE: OFF', (self.cfg/'rules/model-routing.md').read_text())
        self.assertNotIn('model', json.loads((self.cfg/'settings.json').read_text()))
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertIn('OFF', self.cli('status').stdout)
        self.assertEqual(self.cli('on','--apply').returncode, 0)
        self.assertIn('ROUTING_STATE: ON', (self.cfg/'rules/model-routing.md').read_text())
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['model'],'sonnet')
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertEqual(self.cli('uninstall','--apply').returncode, 0)
        self.assertFalse((self.cfg/'rules/model-routing.md').exists())

    def test_preexisting_manual_opus_remains_when_off(self):
        self.cfg.mkdir()
        (self.cfg/'settings.json').write_text(json.dumps({'model':'opus', 'custom':True}))
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        self.assertEqual(self.cli('off','--apply').returncode, 0)
        settings=json.loads((self.cfg/'settings.json').read_text())
        self.assertEqual(settings['model'], 'opus')
        self.assertEqual(self.cli('on','--apply').returncode, 0)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['model'], 'opus')
        self.assertEqual(self.cli('uninstall','--apply').returncode, 0)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text()), {'model':'opus', 'custom':True})

    def test_toggle_previews_no_mutations_and_idempotence(self):
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        state_path=self.cfg/'office-os-routing/state.json'
        prior=state_path.read_bytes()
        self.assertIn('PREVIEW ONLY', self.cli('off').stdout)
        self.assertEqual(state_path.read_bytes(), prior)
        self.assertEqual(self.cli('off','--apply').returncode, 0)
        disabled=state_path.read_bytes()
        repeated=self.cli('off','--apply')
        self.assertIn('ALREADY OFF', repeated.stdout)
        self.assertEqual(disabled,state_path.read_bytes())
        self.assertIn('PREVIEW ONLY', self.cli('on').stdout)
        self.assertEqual(disabled,state_path.read_bytes())

    def test_reinstall_does_not_silently_reenable(self):
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        self.assertEqual(self.cli('off','--apply').returncode, 0)
        self.assertEqual(self.cli('install','--apply').returncode, 0)
        self.assertIn('ROUTING_STATE: OFF', (self.cfg/'rules/model-routing.md').read_text())
        self.assertNotIn('model', json.loads((self.cfg/'settings.json').read_text()))
        self.assertEqual(self.cli('verify').returncode,0)
        self.assertEqual(self.cli('uninstall','--apply').returncode,0)
        self.assertFalse((self.cfg/'commands/dynamic-routing.md').exists())

    def test_tampered_rule_blocks_toggle(self):
        self.assertEqual(self.cli('install','--apply').returncode,0)
        rule=self.cfg/'rules/model-routing.md'
        rule.write_text(rule.read_text()+'\nmy custom instructions\n')
        result=self.cli('off','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('refusing to overwrite',result.stderr)
        self.assertIn('my custom instructions',rule.read_text())

    def test_rollback_after_off_restores_on(self):
        self.assertEqual(self.cli('install','--apply').returncode,0)
        self.assertEqual(self.cli('off','--apply').returncode,0)
        self.assertEqual(self.cli('rollback','--apply').returncode,0)
        self.assertEqual(self.cli('status').returncode,0)
        self.assertIn('ON',self.cli('status').stdout)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['model'], 'sonnet')
        self.assertEqual(self.cli('verify').returncode,0)

    def test_fixed_ownership_manifest_preserves_later_custom_office_files(self):
        self.assertEqual(self.cli('install','--apply').returncode,0)
        custom=self.cfg/'skills/office-os/references/custom-user-workflow.md'
        custom.write_text('USER DATA')
        installed=self.cfg/'skills/office-os/routing-tools/routing_manager.py'
        result=subprocess.run([sys.executable,str(installed),'install','--apply','--config-dir',str(self.cfg)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(custom.read_text(),'USER DATA')
        self.assertEqual(self.cli('uninstall','--apply').returncode,0)
        self.assertEqual(custom.read_text(),'USER DATA')

    def test_status_uninstalled_fails_truthfully(self):
        result=self.cli('status')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('NOT INSTALLED',result.stdout)

if __name__ == '__main__':
    unittest.main()
