# Command Reference

This is the single list of commands. Other docs link here.

## Skill

| Command | What it does |
|---|---|
| `/office-os` | Start the main skill for features, bugs, audits, incidents and releases |
| `/office-os routing <command>` | Run any manager command below from inside Claude Code (it previews first) |

The `/office:*` workflow names (for example `/office:bug` or `/office:release`) are a descriptive map, not registered commands. See [command-surface.md](../office-os/references/command-surface.md).

## Routing control (`/dynamic-routing`)

| Command | What it does |
|---|---|
| `/dynamic-routing status` | Show whether routing is on |
| `/dynamic-routing on` / `off` | Turn routing on or off (open a new session afterwards) |
| `/dynamic-routing profile` | Show the current profile |
| `/dynamic-routing profile economy\|balanced\|quality` | Choose cheaper or deeper routing |
| `/dynamic-routing fallback status` | Show the fallback chain |
| `/dynamic-routing fallback none\|sonnet\|sonnet-haiku` | Set the fallback chain. Applies to all subagents, so it asks first |
| `/dynamic-routing compatibility` | Check your Claude Code version |
| `/dynamic-routing usage <path>` | Summarize usage and estimated cost from a Claude Code JSON result. Nothing is stored unless you add `--record` |
| `/dynamic-routing history` | Show opt-in usage summaries you recorded earlier |
| `/dynamic-routing export` | Save routing preferences (no secrets) to a new file you name |

## Manage / Uninstall

The slash commands above call a small manager script. You can also run it yourself, for example when Claude Code is not available.

```bash
# Installed copy (Linux / macOS / WSL)
python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py <command>

# From a cloned repository
python3 office-os/routing-tools/routing_manager.py <command>
```

On Windows PowerShell, use `py -3` instead of `python3`.

Anything that changes files is a **preview** until you add `--apply`.

| Command | What it does |
|---|---|
| `plan` | Preview what an install would change (the default) |
| `install --apply` | Install or upgrade. Same as `./install.sh --apply` |
| `verify` | Static check of the installed files. It does not prove which model ran |
| `diagnose` | Look for settings that could override routing, and report conflicts |
| `status` | Show whether routing is on or off |
| `on --apply` / `off --apply` | Turn routing on or off |
| `profile [economy\|balanced\|quality] [--apply]` | Show or change the profile |
| `fallback [status\|none\|sonnet\|sonnet-haiku] [--apply]` | Show or change the fallback chain |
| `compatibility [--strict]` | Check the Claude Code version. `--strict` fails if Claude Code is not found |
| `usage --input result.json [--budget-usd N] [--record]` | Summarize a Claude Code JSON result. `--record` saves a sanitized summary locally |
| `history [--limit N]` | Show the last N recorded summaries (default 10) |
| `export --output file.json` | Write a nonsecret snapshot of your routing preferences. It refuses to overwrite an existing file |
| `rollback [--backup DIR] [--apply]` | Restore the files from a backup |
| `uninstall [--apply]` | Remove Office OS routing and restore what was there before |

### Options

| Option | What it does |
|---|---|
| `--apply` | Actually make the change. Without it you only see a preview |
| `--config-dir DIR` | Use another config folder instead of `~/.claude` (`CLAUDE_CONFIG_DIR` works too) |
| `--backup DIR` | With `rollback`: the backup to restore. Default is the most recent install backup |
| `--claude-native` | With `verify`: also ask the Claude CLI to validate the agents |
| `--replace` | Replace conflicting files. Only if you approve replacing all of them |
| `--replace-status-lines` | Replace your existing status-line settings |
| `--set-main-model` | Set an existing main model to Sonnet |

### Remove Office OS

```bash
python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py uninstall           # preview
python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py uninstall --apply   # remove
```

- Files the installer added are removed. Files it replaced are put back.
- If you edited an installed file since, uninstall stops and lists it. Nothing is lost.
- If the installer set your main model to Sonnet because you had none, that setting is removed again.
- A backup of the state before removal is kept.

### Undo a change

```bash
python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py rollback            # preview
python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py rollback --apply
```

- Rollback restores the most recent backup. Use `--backup DIR` to pick another one.
- It refuses to overwrite files you changed after that backup.
- Backups live in `~/.claude/office-os-routing/backups/`. Only the 20 most recent are kept, plus the first install backup (your original settings).
- Backups can contain your full `settings.json`. Do not share them.

Day-to-day steps for assistants: [OPERATIONS.md](../office-os/routing-tools/OPERATIONS.md).
