import json
import os
from pathlib import Path
import unittest

try:  # works for `discover -s tests` and `python -m unittest tests.<module>`
    from _helpers import MANAGER, SMOKE, STATUSLINE, USAGE, ConfigDirCase, run
except ImportError:
    from tests._helpers import MANAGER, SMOKE, STATUSLINE, USAGE, ConfigDirCase, run

class RoutingFeatures(ConfigDirCase):
    def install(self):
        r=self.cli('install','--apply')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def state(self):
        return json.loads((self.cfg/'office-os-routing/state.json').read_text())
    def test_profiles_are_persisted_and_appended_to_auto_rule(self):
        self.install()
        self.assertEqual(self.state()['profile'],'balanced')
        for name in ('economy','quality','balanced'):
            plan=self.cli('profile',name)
            if name!=self.state()['profile']:
                self.assertIn('PREVIEW ONLY',plan.stdout)
            result=self.cli('profile',name,'--apply')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(self.state()['profile'],name)
            self.assertIn('PROFILE_STATE: '+name.upper(),(self.cfg/'rules/model-routing.md').read_text())
            self.assertEqual(self.cli('verify').returncode,0)
    def test_invalid_profile_cannot_change_state(self):
        self.install()
        before=(self.cfg/'office-os-routing/state.json').read_bytes()
        self.assertNotEqual(self.cli('profile','premium','--apply').returncode,0)
        self.assertEqual(before,(self.cfg/'office-os-routing/state.json').read_bytes())
    def test_profile_rollback(self):
        self.install()
        self.assertEqual(self.cli('profile','quality','--apply').returncode,0)
        self.assertEqual(self.cli('rollback','--apply').returncode,0)
        self.assertEqual(self.state()['profile'],'balanced')
        self.assertIn('PROFILE_STATE: BALANCED',(self.cfg/'rules/model-routing.md').read_text())
    def test_profile_off_then_on_uses_selected_profile(self):
        self.install()
        self.assertEqual(self.cli('off','--apply').returncode,0)
        self.assertEqual(self.cli('profile','economy','--apply').returncode,0)
        self.assertIn('ROUTING_STATE: OFF',(self.cfg/'rules/model-routing.md').read_text())
        self.assertEqual(self.cli('on','--apply').returncode,0)
        self.assertIn('PROFILE_STATE: ECONOMY',(self.cfg/'rules/model-routing.md').read_text())
    def test_default_fallback_does_not_modify_settings(self):
        self.install()
        settings=json.loads((self.cfg/'settings.json').read_text())
        self.assertNotIn('fallbackModel',settings)
    def test_fallback_previews_apply_and_restore_user_original(self):
        self.cfg.mkdir()
        (self.cfg/'settings.json').write_text(json.dumps({'fallbackModel':['haiku'],'model':'opus','custom':{'preserve':True}}))
        self.install()
        p=self.cli('fallback','sonnet')
        self.assertIn('PREVIEW ONLY',p.stdout)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['fallbackModel'],['haiku'])
        self.assertEqual(self.cli('fallback','sonnet','--apply').returncode,0)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['fallbackModel'],['sonnet'])
        self.assertEqual(self.cli('fallback','none','--apply').returncode,0)
        self.assertNotIn('fallbackModel',json.loads((self.cfg/'settings.json').read_text()))
        self.assertEqual(self.cli('uninstall','--apply').returncode,0)
        restored=json.loads((self.cfg/'settings.json').read_text())
        self.assertEqual(restored['fallbackModel'],['haiku'])
        self.assertEqual(restored['model'],'opus')
        self.assertEqual(restored['custom'],{'preserve':True})
    def test_safe_fallback_rollback(self):
        self.install()
        self.assertEqual(self.cli('fallback','sonnet-haiku','--apply').returncode,0)
        self.assertEqual(json.loads((self.cfg/'settings.json').read_text())['fallbackModel'],['sonnet','haiku'])
        self.assertEqual(self.cli('verify').returncode,0)
        self.assertEqual(self.cli('rollback','--apply').returncode,0)
        self.assertNotIn('fallbackModel',json.loads((self.cfg/'settings.json').read_text()))
    def test_existing_premium_fallback_is_detected(self):
        self.install()
        path=self.cfg/'settings.json'; d=json.loads(path.read_text()); d['fallbackModel']=['fable']; path.write_text(json.dumps(d))
        out=self.cli('verify')
        self.assertNotEqual(out.returncode,0)
        self.assertIn('approval-only Fable',out.stdout)
        self.assertEqual(self.cli('fallback','none','--apply').returncode,0)
        self.assertEqual(self.cli('verify').returncode,0)
    def test_fallback_preview_cannot_modify_state(self):
        self.install(); old=(self.cfg/'office-os-routing/state.json').read_bytes()
        self.assertIn('PREVIEW ONLY',self.cli('fallback','sonnet').stdout)
        self.assertEqual(old,(self.cfg/'office-os-routing/state.json').read_bytes())
    @unittest.skipIf(os.name == "nt", "POSIX fake CLI executable; Windows installer is tested separately in CI")
    def test_compatibility_fake_claude_version(self):
        fake=Path(self.tmp.name)/'bin';fake.mkdir()
        cmd=fake/'claude';cmd.write_text('#!/bin/sh\necho "2.1.284 (Claude Code)"\n');cmd.chmod(0o755)
        env=dict(self.env,PATH=str(fake)+os.pathsep+os.getenv('PATH',''))
        p=run([MANAGER,'compatibility','--strict','--config-dir',self.cfg],env=env)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('PASS',p.stdout)
        cmd.write_text('#!/bin/sh\necho "2.1.200 (Claude Code)"\n')
        q=run([MANAGER,'compatibility','--strict','--config-dir',self.cfg],env=env)
        self.assertEqual(q.returncode,1)
    def test_usage_reports_actual_model_keys_and_budget(self):
        path=Path(self.tmp.name)/'claude.jsonl'
        raw={'type':'result','total_cost_usd':0.5,'result':'PRIVATE PROMPT OUTPUT DO NOT SAVE','modelUsage':{'claude-sonnet-x':{'inputTokens':10,'outputTokens':5,'costUSD':0.3},'claude-haiku-x':{'inputTokens':3,'outputTokens':2,'costUSD':0.2}}}
        path.write_text(json.dumps(raw)+'\n'+json.dumps(raw)+'\n')
        self.install()
        p=self.cli('usage','--input',str(path),'--budget-usd','0.8','--record')
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('BUDGET WARNING',p.stdout)
        self.assertIn('claude-haiku-x',p.stdout)
        history=(self.cfg/'office-os-routing/usage-history.jsonl').read_text()
        self.assertNotIn('PRIVATE PROMPT OUTPUT',history)
        self.assertEqual(len(history.strip().splitlines()),1)
    def test_usage_rejects_input_without_result(self):
        src=Path(self.tmp.name)/'fake.json';src.write_text(json.dumps({'type':'assistant','message':'NOT A RESULT'}))
        q=run([USAGE,src],env=self.env)
        self.assertEqual(q.returncode,1)
    def test_live_smoke_is_dry_run_by_default(self):
        r=run([SMOKE],env=self.env)
        self.assertEqual(r.returncode,0)
        self.assertIn('DRY RUN',r.stdout)
    def test_statusline_cost_and_profile_are_observed_only(self):
        self.install()
        payload={'model':{'display_name':'Sonnet'},'cost':{'total_cost_usd':1.256}}
        status=STATUSLINE
        out=run([status],input=json.dumps(payload),env=self.env)
        self.assertIn('est. API: $1.26',out.stdout)
        self.assertIn('routing: balanced',out.stdout)
        self.assertEqual(self.cli('off','--apply').returncode,0)
        off=run([status],input=json.dumps(payload),env=self.env)
        self.assertIn('routing: OFF',off.stdout)

    def test_export_is_sanitized_and_does_not_overwrite(self):
        self.cfg.mkdir()
        (self.cfg/'settings.json').write_text(json.dumps({'privateKey':'DO-NOT-EXPORT','fallbackModel':['sonnet']}))
        self.install()
        dest=Path(self.tmp.name)/'export.json'
        self.assertEqual(self.cli('export','--output',str(dest)).returncode,0)
        self.assertNotIn('DO-NOT-EXPORT',dest.read_text())
        self.assertEqual(json.loads(dest.read_text())['profile'],'balanced')
        self.assertNotEqual(self.cli('export','--output',str(dest)).returncode,0)

    def test_history_does_not_record_automatically(self):
        self.install()
        self.assertIn('NO HISTORY',self.cli('history').stdout)
        self.assertFalse((self.cfg/'office-os-routing/usage-history.jsonl').exists())

    def test_installed_manager_includes_new_scripts(self):
        self.install()
        installed=self.cfg/'skills/office-os/routing-tools'
        self.assertTrue((installed/'usage_report.py').is_file())
        self.assertTrue((installed/'scripts/live_smoke.py').is_file())
        self.assertEqual(run([installed/'routing_manager.py','profile','--config-dir',self.cfg],env=self.env).returncode,0)

if __name__=='__main__': unittest.main()
