# Install Office OS with integrated Claude Dynamic Routing v4

**Office OS is the main skill.** This distribution installs one `/office-os` skill, its full original references, global model-routing policy, Haiku/Opus subagents and native model status display. Automatic routing is ON by default. `/dynamic-routing` is a control-only command with `off`, `on`, and `status`, not a competing skill.

## Safe installation (preview first)

Linux/macOS/WSL:

```bash
./install.sh                # preview ONLY
./install.sh --apply        # install after reviewing preview
./verify.sh                # static checks
```

Windows PowerShell (Python 3 required):

```powershell
.\install.ps1
.\install.ps1 --apply
.\verify.ps1
```

Existing user settings, unrelated agents and status lines are preserved by default. For a customized pre-existing `office-os` skill or conflicting user rule/agent, the installer STOPS instead of overwriting. Only use `--replace` if you deliberately approve replacing all reported conflicting package-owned files. Exact pristine Office OS files and pristine v3 routing files can be upgraded with backup.

If you have **standalone Dynamic Routing v4 installed**, first use its own manager to preview and uninstall it. The integrated installer blocks concurrent installations to avoid competing global policies. Your v4 backups remain available.

`CLAUDE_CONFIG_DIR` and `--config-dir` are supported. Installing does not modify an existing `CLAUDE.md`. A new user-level main model is set to Sonnet only if none is already configured, unless you explicitly request `--set-main-model`.

Restart Claude Code as needed; automatic routing applies even without invoking `/office-os`. Use `/dynamic-routing off`, `/dynamic-routing on`, or `/dynamic-routing status` as needed. Restart after toggling for guaranteed rule refresh. Invoke `/office-os` for cross-functional work. To manage routing, request `/office-os routing diagnose`, `/office-os routing verify`, or `/office-os routing plan`. In environments without shell execution, use the installed `~/.claude/skills/office-os/routing-tools/routing_manager.py` directly.

Static verification does **not** prove actual model execution. See `office-os/routing-tools/SMOKE_TESTS.md` for opt-in live checks.

## Advanced routing management (v4.3)

After installation, `/dynamic-routing on|off|status` and `/dynamic-routing profile economy|balanced|quality` work through the installed Office OS manager. Availability fallback is opt-in because it can affect all subagents; `/dynamic-routing fallback status` shows the current setting. `/dynamic-routing compatibility` checks CLI support. See `office-os/routing-tools/RELEASE_CHECKLIST.md` for authenticated live tests and native Windows/macOS release steps.
