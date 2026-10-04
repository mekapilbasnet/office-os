# Office OS: routing management

This is the on-demand management procedure **inside** `/office-os`, not a second skill. The persistent user rule is independent of skill invocation.

When a user requests `/office-os routing <command>`:

1. Locate `routing-tools/routing_manager.py` relative to this installed SKILL.md. If missing, use the explicitly provided extracted package; never invent a filesystem path.
2. Commands: `plan` (default), `install`, `verify`, `diagnose`, `rollback`, `uninstall`, `compatibility`, `profile`, `fallback`, `usage`, or `smoke-test`. For every modifying command, run read-only preview first.
3. Linux/macOS/WSL: `python3 <manager> <command>`; Windows: `py -3 <manager> <command>` (or installed Python 3). Respect the user's `--config-dir` if supplied.
4. Never run `--apply`, `--replace`, `--replace-status-lines`, or `--set-main-model` without approval matching the requested operation. For existing unrelated configuration, prefer to preserve it.
5. `verify` is static. `diagnose` reads accessible config and flags potential overrides but cannot prove actual runtime model selection. Never print settings secrets or full backups.
6. For rollback, show the backup and preview first; refuse to clobber later user edits. For smoke-test, read `SMOKE_TESTS.md` beside the manager, do not pass `smoke-test` to it, and obtain permission before live tests that consume model usage.
7. If prior standalone Dynamic Routing v4 is installed, first preview and uninstall it with its original manager; do not stack conflicting always-on policies. The Office OS installer detects and refuses that state. Pristine v3 policy/agents can be upgraded directly.
8. Don't claim a skill can force the main model, override managed/project settings, or guarantee premium-model approval against manual user overrides.

For everyday Office OS work, see `references/model-routing.md`.

## Automatic activation and direct on/off commands

The global rule `~/.claude/rules/model-routing.md` applies automatically to regular Claude Code sessions. The installer creates it in ON mode by default. `/dynamic-routing` is a lightweight legacy slash command installed under `~/.claude/commands/`, not another routing skill. Run `/dynamic-routing off`, `/dynamic-routing on`, or `/dynamic-routing status`; these delegate to this installed manager. The explicit `on`/`off` command authorizes just that change. To make it effective across all preloaded instructions, open a new Claude Code session after toggling. Status-line observability and existing manually chosen models are untouched.

Equivalent CLI: `python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py off --apply` (or `on --apply`, `status`).

## v4.3 profile and usage controls

- `/dynamic-routing profile economy|balanced|quality`: explicit user selection updates the guarded global rule and state; changes are previewable and reversible. `profile` alone reports current profile.
- `/dynamic-routing fallback status|none|sonnet|sonnet-haiku`: never silently modify an existing fallback. Changing fallback is opt-in and requires approval because it applies to all subagents. There is no Fable in the proposed chains.
- `/office-os routing compatibility`: checks the installed CLI's version (recommended >= 2.1.257); use `--strict` for CI on real target hardware.
- `/office-os routing usage --input result.json [--budget-usd N]`: offline summary from `claude -p --output-format json` result objects; `--record` opt-in stores only sanitized numeric summaries locally. The warning threshold cannot cap billing.
- The opt-in test runner is `routing-tools/scripts/live_smoke.py`. It requires both `--run` and `--approve-usage` and does not claim per-agent model attribution from aggregate modelUsage.

- `history`: display only sanitized usage snapshots previously recorded by opt-in `usage --record`. This is not an automatic task-decision log.
- `export --output path.json`: create a nonsecret portable settings snapshot (profile, routing state, and recognized fallback). Import is intentionally manual to avoid overwriting a different computer's local settings.
