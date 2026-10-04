---
description: Manually enable, disable, or inspect Office OS automatic model routing. Use `/dynamic-routing on`, `/dynamic-routing off`, `/dynamic-routing status`, `/dynamic-routing profile economy|balanced|quality`, or `/dynamic-routing fallback status|none|sonnet|sonnet-haiku`.
disable-model-invocation: true
---

# Toggle Office OS automatic model routing

User command: `/dynamic-routing $ARGUMENTS`

This is a **control-only alias** for the Office OS routing manager. It is not a second routing policy or orchestration skill. The user invoking `on` or `off` explicitly authorizes that toggle, but nothing else. Parse `$ARGUMENTS` exactly:

- `off`: execute `python3 "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/office-os/routing-tools/routing_manager.py" off --apply` in Bash-compatible shells; for PowerShell, use `python "$env:CLAUDE_CONFIG_DIR/skills/office-os/routing-tools/routing_manager.py" off --apply` when set, or the path under `$HOME/.claude`. Do not run a setup or install in its place.
- `on`: use the same installed manager path with `on --apply`.
- `status` or no argument: use the same manager path with `status` (read-only).
- `profile` with no value: run `profile` read-only. `profile economy|balanced|quality`: run the manager with `profile <name> --apply`; the user's explicit command authorizes only the selected profile change.
- `fallback status`: inspect only. `fallback none|sonnet|sonnet-haiku`: first show that this changes user-level fallback settings for **all** subagents; get explicit approval before running the manager with `fallback <choice> --apply`.
- `usage <path>`: run the manager with `usage --input <path>` on an explicitly provided Claude Code JSON output. Never persist the input or prompts. Record only if the user separately authorizes `--record`.
- `compatibility`: run the manager with `compatibility` read-only.
- `history`: show opt-in sanitized usage summaries; `export` requires an explicit output file and writes only nonsecret routing preferences.
- Anything else: explain the supported subcommands without running anything.

Use an execution tool available in Claude Code; if execution is not permitted, say the toggle was **not** applied and show the exact shell command instead. Read the manager result and only report success if it reports completion. Do not claim live model switching. For the remainder of the current conversation, obey the user's updated routing preference immediately. To guarantee automatic rule refresh across the full Claude Code session, start a new session after toggling.
