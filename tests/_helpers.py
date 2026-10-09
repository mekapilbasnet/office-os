"""Shared helpers for the offline test suite (stdlib only)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'office-os/routing-tools'
MANAGER = TOOLS / 'routing_manager.py'
USAGE = TOOLS / 'usage_report.py'
SKILLS_CHECK = TOOLS / 'skills_check.py'
SMOKE = TOOLS / 'scripts/live_smoke.py'
STATUSLINE = TOOLS / 'scripts/statusline.py'
SUBAGENT_STATUSLINE = TOOLS / 'scripts/subagent_statusline.py'
TIMEOUT = 60


def run(args, input=None, env=None, timeout=TIMEOUT):
    """Run a script with the current interpreter; text mode, always with a timeout."""
    return subprocess.run([sys.executable, *[str(a) for a in args]], input=input, capture_output=True,
                          text=True, encoding='utf-8', errors='replace', env=env, timeout=timeout)


class ConfigDirCase(unittest.TestCase):
    """Gives each test a private config dir and an environment that never sees the real ~/.claude."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'home'
        self.home.mkdir()
        self.cfg = Path(self.tmp.name) / '.claude'
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.cfg), HOME=str(self.home), USERPROFILE=str(self.home))

    def cli(self, *args):
        return run([MANAGER, *args, '--config-dir', self.cfg], env=self.env)


def run_bytes(args, data, env=None, timeout=TIMEOUT):
    """Like run(), but feeds raw bytes on stdin and returns undecoded output (for invalid-UTF-8 cases)."""
    return subprocess.run([sys.executable, *[str(a) for a in args]], input=data, capture_output=True,
                          env=env, timeout=timeout)
