# Release and platform validation checklist

Static validation runs offline. Live verification is not complete until actual authenticated Claude Code requests are observed on the user's target machine.

## Automated offline steps

- `python3 -m unittest discover -s tests -v` from the extracted package
- `./install.sh` in an isolated `CLAUDE_CONFIG_DIR` (preview)
- `./install.sh --apply && ./verify.sh` in that isolated directory
- `python3 ~/.claude/skills/office-os/routing-tools/routing_manager.py compatibility`
- `python3 .../routing_manager.py profile quality` (preview), then `--apply`; confirm rule has `PROFILE_STATE: QUALITY`; rollback; confirm profile reverted
- Test `fallback none|sonnet|sonnet-haiku` preview, activation and rollback against a temporary config only
- Test `off --apply` / `on --apply` including an existing manually chosen main model

## On the user's authenticated Claude Code host

1. Start a fresh session; inspect `/status` and model status line. `compatibility --strict` must pass (recommended v2.1.271+).
2. Make a nontrivial but safe request with routing ON, without invoking `/office-os` explicitly. Inspect `/tasks` and subagent status line for **resolved model ID**, rather than trusting narrated model names.
3. Make sure the selected/default main model is Sonnet if validating the default policy; the smoke runner deliberately does not override the actual configured model. Run `python3 ~/.claude/skills/office-os/routing-tools/scripts/live_smoke.py` to preview. Run with `--run --approve-usage --output smoke-evidence.json` only with permission to spend usage.
4. Review sanitized model-use evidence; correlate with `/tasks` or task panel. Presence of Haiku/Opus in `modelUsage` alone does not establish which agent used them.
5. Temporarily test unavailability/fallback in an isolated configuration on an authorized provider; check actual model and make sure Fable isn't added to fallback. Never intentionally disrupt a production session.
6. In native PowerShell on Windows and zsh/Bash on macOS, run preview, install, verify, on/off, profile, rollback and uninstall in a temporary `CLAUDE_CONFIG_DIR` and record their exit codes.
7. Confirm existing custom settings, CLAUDE.md files and status-line customization survive upgrades, and a fresh session reflects on/off and profile selection.

## Truthful release labels

- `STATIC PASSED`: syntax, file safety, simulated fallback/CLI and offline regression tests passed
- `LIVE PARTIAL`: a real run's effective modelUsage is captured but per-agent resolved IDs weren't observed
- `LIVE VERIFIED`: effective main and each test subagent model were independently observed and recorded
- `PLATFORM UNVERIFIED`: any OS not actually tested on that OS; a Unix-shell Windows compatibility check is insufficient

## Optional CI infrastructure

The `.github/workflows/ci.yml` file runs offline tests and platform-specific installer smoke tests on the three hosted operating systems after the project is published to GitHub and Actions is enabled. A workflow file is not evidence that macOS or Windows tests were executed. Record the CI job URLs before marking either platform verified.
