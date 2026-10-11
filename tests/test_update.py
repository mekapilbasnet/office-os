"""`update`: find the local copy (recorded, else the standard folder), pull, install and verify.

Uses throwaway local git repositories only; never the network or the real ~/.claude.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import unittest

from _helpers import ConfigDirCase, ROOT, run

GIT = shutil.which('git')
WORKFLOWS = 'office-os/references/workflows.md'
INSTALLED_WORKFLOWS = 'skills/office-os/references/workflows.md'


def git(*args, cwd=None):
    result = subprocess.run([GIT, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *args],
                            cwd=cwd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise AssertionError(f'git {args}: {result.stderr}')
    return result.stdout.strip()


def force_remove(folder):
    """rmtree that also removes git's read-only object files on Windows."""
    def retry(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(folder, onerror=retry)


@unittest.skipUnless(GIT, 'git not installed')
class UpdateCommand(ConfigDirCase):
    def setUp(self):
        super().setUp()
        base = Path(self.tmp.name).resolve()
        self.home = self.home.resolve()
        self.cfg = self.cfg.resolve()
        self.env['CLAUDE_CONFIG_DIR'] = str(self.cfg)
        # Upstream: a git repository holding the package files from this working tree.
        self.upstream = base / 'upstream'
        shutil.copytree(ROOT / 'office-os', self.upstream / 'office-os',
                        ignore=shutil.ignore_patterns('__pycache__'))
        # Keep LF line endings like the real repository, even where git's autocrlf is on (Windows CI).
        shutil.copy(ROOT / '.gitattributes', self.upstream / '.gitattributes')
        git('init', '--quiet', cwd=self.upstream)
        git('add', '.', cwd=self.upstream)
        git('commit', '--quiet', '-m', 'initial', cwd=self.upstream)
        self.env['OFFICE_OS_REPOSITORY'] = str(self.upstream)
        self.standard = self.home / '.office-os'

    def clone(self, dest):
        git('clone', '--quiet', str(self.upstream), str(dest))
        return dest

    def install_from(self, copy):
        result = run([copy / 'office-os/routing-tools/routing_manager.py', 'install', '--apply',
                      '--config-dir', self.cfg], env=self.env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def update(self, *extra):
        installed = self.cfg / 'skills/office-os/routing-tools/routing_manager.py'
        return run([installed, 'update', *extra, '--config-dir', self.cfg], env=self.env, timeout=180)

    def publish_change(self):
        path = self.upstream / WORKFLOWS
        path.write_bytes(path.read_bytes() + b'\nNew upstream line.\n')
        git('commit', '--quiet', '-am', 'change', cwd=self.upstream)

    def state(self):
        return json.loads((self.cfg / 'office-os-routing/state.json').read_text())

    def test_install_records_its_copy_and_update_uses_it(self):
        copy = self.clone(Path(self.tmp.name).resolve() / 'somewhere/office-os')
        self.install_from(copy)
        self.assertEqual(self.state()['source'], str(copy))
        self.publish_change()

        preview = self.update()
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertIn(str(copy), preview.stdout)
        self.assertIn('1 new change', preview.stdout)
        self.assertNotIn(b'New upstream line', (self.cfg / INSTALLED_WORKFLOWS).read_bytes())
        self.assertNotEqual(git('rev-parse', 'HEAD', cwd=copy), git('rev-parse', 'HEAD', cwd=self.upstream))

        applied = self.update('--apply')
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertIn('UPDATED', applied.stdout)
        self.assertIn(b'New upstream line', (self.cfg / INSTALLED_WORKFLOWS).read_bytes())
        self.assertEqual(git('rev-parse', 'HEAD', cwd=copy), git('rev-parse', 'HEAD', cwd=self.upstream))
        self.assertFalse(self.standard.exists())

        again = self.update()
        self.assertIn('UP TO DATE', again.stdout)
        again = self.update('--apply')
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn('UP TO DATE: no newer version', again.stdout)

    def test_missing_copy_downloads_into_standard_folder(self):
        copy = self.clone(Path(self.tmp.name).resolve() / 'temporary/office-os')
        self.install_from(copy)
        force_remove(copy)
        self.publish_change()

        preview = self.update()
        self.assertIn('NO LOCAL COPY', preview.stdout)
        self.assertFalse(self.standard.exists())

        applied = self.update('--apply')
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        self.assertTrue((self.standard / '.git').exists())
        self.assertIn(b'New upstream line', (self.cfg / INSTALLED_WORKFLOWS).read_bytes())
        self.assertEqual(self.state()['source'], str(self.standard))

    def test_standard_folder_found_when_nothing_recorded(self):
        self.install_from(self.clone(self.standard))
        state = self.state()
        state.pop('source')
        (self.cfg / 'office-os-routing/state.json').write_text(json.dumps(state))
        preview = self.update()
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        self.assertIn(str(self.standard), preview.stdout)

    def test_foreign_standard_folder_is_never_overwritten(self):
        copy = self.clone(Path(self.tmp.name).resolve() / 'temporary/office-os')
        self.install_from(copy)
        force_remove(copy)
        self.standard.mkdir()
        (self.standard / 'notes.txt').write_text('mine')
        result = self.update('--apply')
        self.assertEqual(result.returncode, 1)
        self.assertIn('not an Office OS git copy', result.stderr)
        self.assertEqual(os.listdir(self.standard), ['notes.txt'])

    def test_moved_copy_is_remembered_without_a_new_backup(self):
        first = self.clone(Path(self.tmp.name).resolve() / 'first/office-os')
        self.install_from(first)
        backups = sorted(os.listdir(self.cfg / 'office-os-routing/backups'))
        second = self.clone(Path(self.tmp.name).resolve() / 'second/office-os')
        self.install_from(second)
        self.assertEqual(self.state()['source'], str(second))
        self.assertEqual(sorted(os.listdir(self.cfg / 'office-os-routing/backups')), backups)

    def test_update_before_install_is_a_clean_error(self):
        result = run([self.upstream / 'office-os/routing-tools/routing_manager.py', 'update', '--apply',
                      '--config-dir', self.cfg], env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn('not installed', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
