# Installation Guide

This is the detailed install reference. For the quick version, see the [README](../README.md).

Office OS is the main skill. One install gives you the `/office-os` skill, its references, the global model-routing rule, the Haiku, Opus and reviewer subagents, and the model status line. Automatic routing is **on** by default. `/dynamic-routing` is a control-only command, not a second skill.

## Requirements

- Claude Code
- Git
- Python 3 (`python3` on Linux/macOS/WSL, `python` or `py` on Windows). No packages needed.

## Install

Easiest: paste this into Claude Code.

```
Install the Office OS skill from https://github.com/mekapilbasnet/office-os
— clone it, then run ./install.sh --apply (or install.ps1 --apply on
Windows), then run ./verify.sh (or .\verify.ps1 on Windows).
```

Linux / macOS / WSL:

```bash
./install.sh          # preview only
./install.sh --apply  # install after reviewing the preview
./verify.sh           # static checks
```

Windows PowerShell:

```powershell
.\install.ps1
.\install.ps1 --apply
.\verify.ps1
```

Restart Claude Code afterwards. Routing applies even if you never type `/office-os`.

## Update

```bash
git pull
./install.sh          # preview
./install.sh --apply
./verify.sh
```

Unchanged files are skipped, changed package files are upgraded with a backup, and your own edits are never overwritten silently.

## What the installer will and will not touch

- Your settings, unrelated agents and custom status lines are kept.
- If you customized an installed Office OS file, or have a conflicting rule or agent, the installer **stops** and lists the conflicts. Use `--replace` only if you approve replacing all of them.
- Exact original Office OS files and original v3 routing files upgrade cleanly, with backup.
- An existing `CLAUDE.md` is never modified.
- A user-level main model is set to Sonnet only if none is configured, unless you pass `--set-main-model`.
- `CLAUDE_CONFIG_DIR` and `--config-dir` choose a different config folder (default `~/.claude`).

## Standalone Dynamic Routing already installed

Preview and uninstall it with its own manager first. The integrated installer refuses to install next to it, so two routing policies never compete. Your backups stay available.

## Managing routing

- `/dynamic-routing on|off|status`, then restart Claude Code so the rule refreshes.
- `/dynamic-routing profile economy|balanced|quality`
- `/dynamic-routing fallback status` (changing the fallback is opt-in and affects all subagents)
- `/dynamic-routing compatibility` checks your Claude Code version.
- `/office-os routing diagnose|verify|plan` for the full manager.
- Without shell access, run `~/.claude/skills/office-os/routing-tools/routing_manager.py` directly.

Full list: [COMMANDS.md](COMMANDS.md).

## Checking it worked

`./verify.sh` is a static check. It does **not** prove which model Claude Code ran. For live checks see [SMOKE_TESTS.md](../office-os/routing-tools/SMOKE_TESTS.md) and [RELEASE_CHECKLIST.md](../office-os/routing-tools/RELEASE_CHECKLIST.md).

## Optional: Ponytail

Office OS routes broad codebase audits to **Ponytail** when it is installed. Not bundled:

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

See https://github.com/DietrichGebert/ponytail.
