import argparse
import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MANAGER = ROOT / 'office-os/routing-tools/routing_manager.py'
spec = importlib.util.spec_from_file_location('manager_hardening_under_test', MANAGER)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)

POSIX = os.name != 'nt'


class HardeningCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.cfg = self.base / '.claude'
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ('CLAUDE_CODE_SUBAGENT_MODEL_FORCE', 'ANTHROPIC_MODEL')}
        self.env['CLAUDE_CONFIG_DIR'] = str(self.cfg)

    def cli(self, *args, **kwargs):
        return subprocess.run([sys.executable, str(MANAGER), *args], capture_output=True, text=True,
                              env=self.env, timeout=60, **kwargs)

    def install(self, *extra):
        result = self.cli('install', '--apply', *extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def settings(self):
        return json.loads((self.cfg / 'settings.json').read_text())

    def state_path(self):
        return self.cfg / 'office-os-routing/state.json'

    def state(self):
        return json.loads(self.state_path().read_text())

    def write_state(self, state):
        self.state_path().write_text(json.dumps(state))

    def backups(self):
        root = self.cfg / 'office-os-routing/backups'
        return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []

    def install_args(self):
        return argparse.Namespace(apply=True, replace=False, replace_status_lines=False, set_main_model=False)


class StateValidation(HardeningCase):
    def test_state_missing_keys_gives_clean_error(self):
        self.state_path().parent.mkdir(parents=True)
        self.write_state({'version': 'x'})
        for command in (('uninstall', '--apply'), ('verify',), ('status',), ('on', '--apply'), ('profile', 'quality', '--apply')):
            result = self.cli(*command)
            self.assertEqual(result.returncode, 1, command)
            self.assertIn('ERROR', result.stderr)
            self.assertIn("missing 'files'", result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_state_with_wrong_types_is_rejected(self):
        self.install()
        state = self.state()
        state['files']['rules/model-routing.md'] = {'oops': 1}
        self.write_state(state)
        result = self.cli('uninstall', '--apply')
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)

    def test_state_path_traversal_is_rejected(self):
        self.install()
        victim = self.base / 'victim.txt'
        victim.write_text('precious')
        state = self.state()
        state['files']['../victim.txt'] = {'installed_sha': manager.sha(b'precious')}
        state['originals']['../victim.txt'] = None
        self.write_state(state)
        result = self.cli('uninstall', '--apply')
        self.assertEqual(result.returncode, 1)
        self.assertIn('outside the Claude config directory', result.stderr)
        self.assertEqual(victim.read_text(), 'precious')
        self.assertTrue(self.state_path().exists())

    def test_backup_path_traversal_is_rejected(self):
        self.install()
        victim = self.base / 'victim.txt'
        evil = self.base / 'evil-backup'
        evil.mkdir()
        record = {'operation': 'install', 'after_hashes': {},
                  'before': {'../victim.txt': base64.b64encode(b'pwned').decode('ascii')}}
        (evil / 'backup.json').write_text(json.dumps(record))
        result = self.cli('rollback', '--apply', '--backup', str(evil))
        self.assertEqual(result.returncode, 1)
        self.assertIn('outside the Claude config directory', result.stderr)
        self.assertFalse(victim.exists())

    def test_absolute_path_is_rejected(self):
        with self.assertRaises(ValueError):
            manager.safe_path(self.cfg, str(self.base / 'abs.txt'))
        with self.assertRaises(ValueError):
            manager.safe_path(self.cfg, '.')
        self.assertEqual(manager.safe_path(self.cfg, 'agents/x.md'), Path(os.path.normpath(self.cfg / 'agents/x.md')))


class ExportHistoryTimeout(HardeningCase):
    def test_export_refuses_to_overwrite(self):
        self.install()
        dest = self.base / 'export.json'
        dest.write_text('KEEP ME')
        result = self.cli('export', '--output', str(dest))
        self.assertEqual(result.returncode, 1)
        self.assertIn('refusing to overwrite', result.stderr)
        self.assertEqual(dest.read_text(), 'KEEP ME')
        fresh = self.base / 'sub/fresh.json'
        self.assertEqual(self.cli('export', '--output', str(fresh)).returncode, 0)
        self.assertEqual(json.loads(fresh.read_text())['profile'], 'balanced')

    def test_history_limit_is_wired(self):
        self.install()
        lines = [json.dumps({'recordedAt': f'2026-01-0{i}', 'reportedTotalCostUSD': i, 'models': {'m': 1}}) for i in range(1, 6)]
        (self.cfg / 'office-os-routing/usage-history.jsonl').write_text('\n'.join(lines) + '\n')
        out = self.cli('history', '--limit', '2').stdout
        self.assertIn('2026-01-05', out)
        self.assertIn('2026-01-04', out)
        self.assertNotIn('2026-01-03', out)
        self.assertNotEqual(self.cli('history', '--limit', '0').returncode, 0)

    def test_native_validation_timeout_is_clean_error(self):
        self.install()
        stderr = io.StringIO()
        argv = ['routing_manager.py', 'verify', '--claude-native', '--config-dir', str(self.cfg)]
        with mock.patch.object(sys, 'argv', argv), \
                mock.patch.object(manager.shutil, 'which', return_value='/fake/claude'), \
                mock.patch.object(manager.subprocess, 'run', side_effect=subprocess.TimeoutExpired('claude', 45)), \
                contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            code = manager.main()
        self.assertEqual(code, 1)
        self.assertIn('timed out', stderr.getvalue())


class BackupsAndUninstall(HardeningCase):
    def test_backups_pruned_to_limit(self):
        self.assertEqual(manager.BACKUP_KEEP, 20)
        self.install()
        for index in range(12):
            for command in ('off', 'on'):
                self.assertEqual(self.cli(command, '--apply').returncode, 0)
        # 20 newest backups plus the oldest install backup, which is never pruned.
        self.assertEqual(len(self.backups()), 21)
        operations = [json.loads((b / 'backup.json').read_text())['operation'] for b in self.backups()]
        self.assertEqual(operations[0], 'install')
        self.assertEqual(operations.count('install'), 1)
        # The newest backup (the one recorded in state) always survives pruning.
        self.assertTrue(Path(self.state()['last_backup']).is_dir())
        self.assertEqual(self.cli('verify').returncode, 0)

    def test_uninstall_removes_empty_dirs_and_restores_settings_exactly(self):
        self.cfg.mkdir()
        original = (json.dumps({'permissions': {'allow': ['Read']}, 'model': 'opus'}, indent=2) + '\n').encode()
        (self.cfg / 'settings.json').write_bytes(original)
        (self.cfg / 'commands').mkdir()
        (self.cfg / 'commands/mine.md').write_text('my command')
        self.install()
        # Running the installed manager can leave bytecode behind; it must not block cleanup.
        self.assertEqual(subprocess.run([sys.executable, str(self.cfg / 'skills/office-os/routing-tools/routing_manager.py'), 'history'],
                                        env=self.env, capture_output=True, timeout=60).returncode, 0)
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual((self.cfg / 'settings.json').read_bytes(), original)
        for name in ('agents', 'rules', 'skills'):
            self.assertFalse((self.cfg / name).exists(), name + ' should be removed when empty')
        self.assertEqual((self.cfg / 'commands/mine.md').read_text(), 'my command')
        self.assertFalse((self.cfg / 'commands/dynamic-routing.md').exists())
        self.assertTrue(self.cfg.is_dir())

    def test_preexisting_empty_directory_is_kept(self):
        (self.cfg / 'agents').mkdir(parents=True)
        self.install()
        self.assertIn('agents', self.state()['created_dirs'] + ['agents'])
        self.assertNotIn('agents', self.state()['created_dirs'])
        self.assertIn('rules', self.state()['created_dirs'])
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertTrue((self.cfg / 'agents').is_dir())
        self.assertFalse((self.cfg / 'agents/Explore.md').exists())
        self.assertFalse((self.cfg / 'rules').exists())
        self.assertFalse((self.cfg / 'skills').exists())

    def test_old_state_without_created_dirs_prunes_only_own_tree(self):
        (self.cfg / 'agents').mkdir(parents=True)
        self.install()
        state = self.state()
        del state['created_dirs']
        self.write_state(state)
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertTrue((self.cfg / 'agents').is_dir())
        self.assertTrue((self.cfg / 'rules').is_dir())  # unknown origin: kept
        self.assertFalse((self.cfg / 'skills/office-os').exists())

    def test_oldest_install_backup_survives_pruning(self):
        self.cfg.mkdir()
        original = b'{"permissions": {"allow": ["Read"]}}\n'
        (self.cfg / 'settings.json').write_bytes(original)
        self.install()
        first = self.backups()[0]
        for index in range(15):
            for command in ('off', 'on'):
                self.assertEqual(self.cli(command, '--apply').returncode, 0)
        self.assertIn(first, self.backups())
        record = json.loads((first / 'backup.json').read_text())
        self.assertEqual(base64.b64decode(record['before']['settings.json']), original)

    def test_uninstall_keeps_directories_with_user_files(self):
        self.install()
        mine = self.cfg / 'agents/mine.md'
        mine.write_text('custom')
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual(mine.read_text(), 'custom')

    def test_interrupted_install_without_state_is_removed_by_uninstall(self):
        # Simulate a process killed after files were written but before state.json was saved.
        script = textwrap.dedent('''
            import importlib.util, os, sys
            spec = importlib.util.spec_from_file_location('m', sys.argv[1])
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            real = m.save
            def killer(path, data, private=None):
                if path.name == 'state.json':
                    os._exit(9)
                real(path, data, private)
            m.save = killer
            sys.argv = ['x', 'install', '--apply']
            m.main()
        ''')
        self.cfg.mkdir()
        original = (json.dumps({'permissions': {'allow': ['Read']}}, indent=2) + '\n').encode()
        (self.cfg / 'settings.json').write_bytes(original)
        killed = subprocess.run([sys.executable, '-c', script, str(MANAGER)], env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(killed.returncode, 9, killed.stdout + killed.stderr)
        self.assertTrue((self.cfg / 'agents/Explore.md').exists())
        self.assertFalse(self.state_path().exists())
        # The killed install already wrote the status lines and the Sonnet default.
        wrote = self.settings()
        self.assertEqual(wrote['model'], 'sonnet')
        self.assertIn('statusLine', wrote)
        self.install()
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual((self.cfg / 'settings.json').read_bytes(), original)
        self.assertFalse((self.cfg / 'agents').exists())
        self.assertFalse((self.cfg / 'rules').exists())
        self.assertFalse((self.cfg / 'skills').exists())


class InstallBehaviour(HardeningCase):
    def test_stale_status_line_path_is_refreshed(self):
        self.install()
        data = self.settings()
        script = str(self.cfg / 'skills/office-os/routing-tools/scripts/statusline.py')
        data['statusLine'] = {'type': 'command', 'command': f'/old/python3 {script}', 'padding': 2}
        (self.cfg / 'settings.json').write_text(json.dumps(data))
        verify = self.cli('verify')
        self.assertIn('outdated', verify.stdout)
        self.install()
        updated = self.settings()['statusLine']
        self.assertEqual(updated['command'], manager.command_line(script))
        self.assertEqual(updated['padding'], 2)
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertNotIn('statusLine', self.settings())

    def test_wrapped_status_line_is_not_ours(self):
        self.cfg.mkdir()
        script = self.cfg / 'skills/office-os/routing-tools/scripts/statusline.py'
        wrapper = {'type': 'command', 'command': f"bash -c 'python3 {script} | colorize'"}
        (self.cfg / 'settings.json').write_text(json.dumps({'statusLine': wrapper}))
        result = self.install()
        self.assertIn('preserved', result.stdout)
        self.assertEqual(self.settings()['statusLine'], wrapper)
        self.assertNotEqual(manager.status_line_kind(self.cfg, self.settings(), 'statusLine'), 'office-os')
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual(self.settings()['statusLine'], wrapper)
        # Extra arguments or a pipe after the script also make it custom.
        for command in (f'python3 {script} --flag', f'python3 {script} | cat', f'cat {script}'):
            self.assertIsNone(manager.package_command_state({'type': 'command', 'command': command}, script), command)
        self.assertIsNone(manager.package_command_state({'type': 'command', 'command': "python3 'unbalanced"}, script))

    def test_stale_refresh_records_real_original(self):
        self.cfg.mkdir()
        script = self.cfg / 'skills/office-os/routing-tools/scripts/statusline.py'
        old = {'type': 'command', 'command': f'/gone/python3 {script}', 'padding': 1}
        (self.cfg / 'settings.json').write_text(json.dumps({'statusLine': old}))
        self.install()
        self.assertEqual(self.state()['settings_originals']['statusLine'], {'existed': True, 'value': old})
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertEqual(self.settings()['statusLine'], old)

    @unittest.skipUnless(POSIX, 'symlinks')
    def test_different_working_interpreter_is_not_stale(self):
        self.install()
        data = self.settings()
        script = self.cfg / 'skills/office-os/routing-tools/scripts/statusline.py'
        other = self.base / 'python-alt'
        other.symlink_to(os.path.realpath(sys.executable))
        data['statusLine'] = {'type': 'command', 'command': f'{other} {script}'}
        (self.cfg / 'settings.json').write_text(json.dumps(data))
        self.assertEqual(manager.status_line_kind(self.cfg, self.settings(), 'statusLine'), 'office-os')
        before = self.backups()
        self.assertIn('ALREADY INSTALLED', self.install().stdout)
        self.assertEqual(self.backups(), before)
        self.assertEqual(self.settings()['statusLine']['command'], f'{other} {script}')
        self.assertNotIn('outdated', self.cli('verify').stdout)

    def test_foreign_status_line_still_preserved(self):
        self.cfg.mkdir()
        base = {'statusLine': {'type': 'command', 'command': 'echo mine'}}
        (self.cfg / 'settings.json').write_text(json.dumps(base))
        result = self.install()
        self.assertIn('preserved', result.stdout)
        self.assertEqual(self.settings()['statusLine'], base['statusLine'])

    def test_rule_has_no_template_blockquote(self):
        self.install()
        rule = (self.cfg / 'rules/model-routing.md').read_text()
        self.assertNotIn('installer template', rule)
        self.assertNotIn('\n> **This is', rule)
        self.assertTrue(rule.startswith('# '))
        self.assertIn('ROUTING_STATE: ON', rule)
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertEqual(self.cli('off', '--apply').returncode, 0)
        self.assertEqual(self.cli('on', '--apply').returncode, 0)
        self.assertEqual(self.cli('profile', 'quality', '--apply').returncode, 0)
        self.assertEqual(self.cli('verify').returncode, 0)
        self.assertEqual(self.cli('status').returncode, 0)

    def test_template_stripping_only_touches_leading_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp)
            (fake / 'references').mkdir()
            (fake / 'tools').mkdir()
            (fake / 'references/model-routing.md').write_text('# Title\n\n> note one\n> note two\n\nBody\n\n> keep this quote\n')
            with mock.patch.object(manager, 'SOURCE', fake / 'tools'):
                self.assertEqual(manager.rule_template().decode(), '# Title\n\nBody\n\n> keep this quote\n')
            (fake / 'references/model-routing.md').write_text('# Title\n\nBody only\n')
            with mock.patch.object(manager, 'SOURCE', fake / 'tools'):
                self.assertEqual(manager.rule_template().decode(), '# Title\n\nBody only\n')

    def test_install_announces_default_model(self):
        result = self.cli('install')
        self.assertIn('no main model', result.stdout)
        self.cfg.mkdir()
        (self.cfg / 'settings.json').write_text(json.dumps({'model': 'opus'}))
        self.assertNotIn('no main model', self.cli('install').stdout)

    def test_interrupt_mid_install_rolls_back(self):
        self.cfg.mkdir()
        original = b'{"permissions": {"allow": ["Read"]}}\n'
        (self.cfg / 'settings.json').write_bytes(original)
        real_save = manager.save
        calls = []
        fired = []

        def interrupting(path, data, private=None):
            calls.append(path.name)
            if len(calls) == 4 and not fired:
                fired.append(True)
                raise KeyboardInterrupt
            real_save(path, data, private)
        with mock.patch.object(manager, 'save', interrupting), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                manager.do_install(self.cfg, self.install_args())
        self.assertGreaterEqual(len(calls), 4)
        self.assertEqual((self.cfg / 'settings.json').read_bytes(), original)
        self.assertFalse(self.state_path().exists())
        self.assertFalse((self.cfg / 'agents/Explore.md').exists())
        self.assertFalse((self.cfg / 'rules/model-routing.md').exists())

    def test_interrupt_during_toggle_restores_state(self):
        self.install()
        before = {p: p.read_bytes() for p in (self.state_path(), self.cfg / 'rules/model-routing.md', self.cfg / 'settings.json')}
        real_save = manager.save
        fired = []

        def interrupting(path, data, private=None):
            if path.name == 'state.json' and not fired:
                fired.append(True)
                raise KeyboardInterrupt
            real_save(path, data, private)
        with mock.patch.object(manager, 'save', interrupting), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                manager.do_toggle(self.cfg, False, True)
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content, path.name)

    @unittest.skipUnless(POSIX, 'POSIX permissions')
    def test_file_modes(self):
        self.install()
        umask = os.umask(0)
        os.umask(umask)
        expected = 0o666 & ~umask
        self.assertEqual((self.cfg / 'agents/Explore.md').stat().st_mode & 0o777, expected)
        self.assertEqual((self.cfg / 'rules/model-routing.md').stat().st_mode & 0o777, expected)
        self.assertEqual(self.state_path().stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.cfg / 'settings.json').stat().st_mode & 0o777, 0o600)
        self.assertEqual(Path(self.state()['last_backup']).joinpath('backup.json').stat().st_mode & 0o777, 0o600)

    @unittest.skipUnless(POSIX, 'symlinks')
    def test_symlinked_settings_written_through(self):
        self.cfg.mkdir()
        target = self.base / 'dotfiles-settings.json'
        target.write_text(json.dumps({'custom': 1}))
        (self.cfg / 'settings.json').symlink_to(target)
        self.install()
        self.assertTrue((self.cfg / 'settings.json').is_symlink())
        self.assertEqual(json.loads(target.read_text())['custom'], 1)
        self.assertIn('statusLine', json.loads(target.read_text()))
        self.assertEqual(self.cli('uninstall', '--apply').returncode, 0)
        self.assertTrue((self.cfg / 'settings.json').is_symlink())
        self.assertEqual(json.loads(target.read_text()), {'custom': 1})

    def test_manifest_has_no_dead_entrypoint_and_min_version_used(self):
        manifest = json.loads((ROOT / 'office-os/routing-tools/manifest.json').read_text())
        self.assertNotIn('entrypoint', manifest)
        self.assertEqual(manager.MIN_CLAUDE, tuple(int(p) for p in manifest['minimum_recommended_claude_code'].split('.')))


if __name__ == '__main__':
    unittest.main()
