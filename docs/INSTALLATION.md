# Installation Guide

This is the single source for install, update and conflict details. The [README](../README.md) has the 3-line version.

Office OS is the main skill. One install gives you the `/office-os` skill, its references, the global model-routing rule, the Haiku, Opus and reviewer subagents, and the model status line. Automatic routing is **on** by default. `/dynamic-routing` is a control-only command, not a second skill.

## Requirements

- Claude Code
- Git
- Python 3.8 or newer (`python3` on Linux/macOS/WSL, `python` or `py` on Windows). No packages needed.

## Install

Easiest: paste this into Claude Code.

```
Install the Office OS skill from https://github.com/mekapilbasnet/office-os
— clone it, then run ./install.sh --apply (or install.ps1 --apply on
Windows), then run ./verify.sh (or .\verify.ps1 on Windows).
```

Linux / macOS / WSL:

```bash
git clone https://github.com/mekapilbasnet/office-os.git
cd office-os
./install.sh          # preview only
./install.sh --apply  # install after reviewing the preview
./verify.sh           # static checks
```

Windows PowerShell:

```powershell
git clone https://github.com/mekapilbasnet/office-os.git
Set-Location office-os
.\install.ps1          # preview only
.\install.ps1 --apply  # install
.\verify.ps1           # static checks
```

If PowerShell blocks the scripts (restricted execution policy), run them like this:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 --apply
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

Restart Claude Code afterwards, then run `/office-os`. Routing applies even if you never type `/office-os`.

## Update

```bash
cd office-os
git pull
./install.sh          # preview
./install.sh --apply
./verify.sh
```

On Windows use `.\install.ps1` and `.\verify.ps1`. Restart Claude Code afterwards.

Unchanged files are skipped, changed package files are upgraded with a backup, and your own edits are never overwritten silently.

## What the installer writes (under `~/.claude`)

- `skills/office-os/`: the skill and its routing tools
- `rules/model-routing.md`: the routing rule (swapped for an OFF rule when disabled)
- `agents/`: the `Explore`, `deep-reasoner` and `reviewer` subagents
- `commands/dynamic-routing.md`: the control command
- Status line settings, only if you have none
- `office-os-routing/`: install state and backups, so changes can be rolled back

To use another folder, set `CLAUDE_CONFIG_DIR` or pass `--config-dir`.

## What the installer will and will not touch

- Your settings, unrelated agents and custom status lines are kept.
- If you customized an installed Office OS file, or have a conflicting rule or agent, the installer **stops** and lists the conflicts. Use `--replace` only if you approve replacing all of them.
- Exact original Office OS files and original v3 routing files upgrade cleanly, with backup.
- An existing `CLAUDE.md` is never modified.
- Main model: if you already set one, it is kept. If you have none, the installer sets `model: sonnet`. `--set-main-model` also switches an existing different model to Sonnet.

## Standalone Dynamic Routing already installed

Preview and uninstall it with its own manager first. The integrated installer refuses to install next to it, so two routing policies never compete. Your backups stay available.

## Managing, rolling back and uninstalling

Turn routing on or off, pick a profile, set a fallback, roll back or uninstall: see [COMMANDS.md](COMMANDS.md#manage--uninstall).

## Checking it worked

`./verify.sh` is a static check. It does **not** prove which model Claude Code ran. For live checks see [SMOKE_TESTS.md](../office-os/routing-tools/SMOKE_TESTS.md) and [RELEASE_CHECKLIST.md](../office-os/routing-tools/RELEASE_CHECKLIST.md).

## Optional extras

**Ponytail** and **Caveman** are not bundled. Office OS uses them only if you install them. Ponytail helps with broad codebase audits; Caveman compresses tokens and gives lean build, fix and review skills.

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

See https://github.com/DietrichGebert/ponytail. Install Caveman from its own project page.
