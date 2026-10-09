# Changelog

All notable changes are listed here, newest first.

## [Unreleased]

### Added
- Update guide, issue and pull request templates, and `CODEOWNERS`.
- CI: Python 3.8 and 3.13 jobs, bundled-skill tests, pyflakes lint, concurrency and timeouts.
- Tests for installer hardening, script robustness and bundled-skill fixes.
- MIT licence text and Phosphor / Google Fonts attributions in `skills/THIRD-PARTY-NOTICES.md`.

### Changed
- Renamed `office-os/routing-tools/agents/` to `subagents/` so it is not confused with `office-os/agents/`. Installed copies keep an unused old `agents` folder after an update; it is safe to delete.
- Reviewer agent now has 30 turns (was 16) so long reviews finish.
- Merged the overlapping install guides: details live in `docs/INSTALLATION.md`, `START_HERE.md` is a short pointer.
- Rewrote the README to be shorter; expanded `docs/ARCHITECTURE.md`.
- Renamed `tests/test_v43.py` to `tests/test_routing_features.py`.
- Installed routing rule no longer includes the "installer template" note; existing installs show as an upgrade on the next install.
- Trimmed the always-on routing rule (about 26% smaller) and stopped Office OS from re-reading it; added a short Reviewer section.
- `routing.md` now describes optional plugins (Caveman, Ponytail, etc.) as "if installed" instead of assuming them.
- Install now says when it sets `model: sonnet` because none was set.
- Minimum recommended Claude Code raised to 2.1.271 (needed by the Explore subagent's `omitClaudeMd`).
- Bundled skills now carry local patches, listed in `skills/THIRD-PARTY-NOTICES.md`.

### Fixed
- Installer: Ctrl-C mid-change now attempts rollback; interrupted installs uninstall cleanly; clear errors for damaged state files and `verify --claude-native` timeouts; stale status-line commands are refreshed when their Python is gone (user-wrapped commands are left alone); uninstall removes empty folders it created; symlinked `settings.json` is written through; backup/state paths are confined to the config folder; `export` refuses to overwrite; only the last 20 backups (plus the first install backup) are kept; `history --limit` works.
- Windows installer/verify scripts handle paths with spaces and stream output; shell scripts check for Python 3.8+.
- Status lines never crash or go blank on malformed input; `live_smoke.py` reads stream-json output (real Task/Agent evidence), handles Windows `claude.cmd`, and no longer passes without delegation evidence; `usage_report.py` handles BOM/UTF-16/bad lines and validates budgets before writing history.
- Bundled skills: icon resizing no longer corrupts stroke width; `ui-ux-pro-max` script paths work outside plugins; no more links to removed skills; brand sync creates `design-tokens.css`, creates `assets/`, uses the real brand name and keeps error colours red; logo batch without `--brand` no longer crashes; generators exit non-zero on failure; API key no longer sent to other hosts; SVG output sanitised; non-Latin project names keep their own folder.
- Docs: uninstall/rollback commands documented; contributor test step uses the throwaway config folder; security reporting link added; Python 3.8+ and Windows execution-policy notes added.

## [1.0.0] - Initial release

- Added a `skills/` bundle (third-party, vendored unmodified): `brand`, `design`, `ui-ux-pro-max`. See `skills/THIRD-PARTY-NOTICES.md`.
- Removed `banner-design`, `slides`, `design-system`, `ui-styling`, `superset` from that bundle as redundant or out of scope; `design` already covered banner/slide generation, `ui-ux-pro-max` already covered tokens/components.
- Added a quick-install option: give Claude the repo URL and it clones + installs + verifies.
- Documented Ponytail as an optional companion (not bundled) for codebase audits and minimal-code generation.
- Dropped the `v4.3` version suffix from the product name in docs and the header image; routing feature version numbers below are unaffected.
- Repo audit fixes: de-duplicated vendored reference files (symlinked, now plain files again after the redundant skills were removed), removed a stray committed coverage artifact, marked `office-os/references/model-routing.md` as the installer template vs. the live rule.
- Actual persisted Economy/Balanced/Quality routing profiles and guarded rollback.
- Explicitly opt-in safe fallback chains, with warnings that fallback also applies to subagents; reject configured automatic Fable fallback during verification.
- Offline per-model usage/cost reports from user-supplied Claude Code result JSON, optional sanitized history, a portable nonsecret config export, and warning threshold.
- CLI compatibility checker, opt-in paid runtime smoke test, and realistic release checklist.
- Preserved a single Office OS skill and automatic routing on/off behavior.
- Added a read-only `reviewer` agent (Sonnet) for independent review of a diff, files, or a plan.
- Added a skills check that reports which optional skills named in the routing guide are installed, plus a templates reference.

### Earlier history

#### Office OS + Dynamic Routing v4 integration

- Preserved all original Office OS skill references and agent metadata.
- Added model routing as an Office OS reference, not a competing second skill.
- Embedded safe installer/verification/rollback into the Office OS skill's routing tools.
- Installed persistent model policy and read-only Haiku/Opus subagents with observability scripts.
- Added backup-safe upgrade from pristine Office OS + pristine v3 routing files.
- Blocked accidental simultaneous install over a separately managed standalone Dynamic Routing setup.
- Preserved existing main model and custom status lines by default.

#### v4.2: automatic activation and toggles

- Automatic model routing ON immediately after installation in new sessions.
- Added `/dynamic-routing off|on|status` control-only command; no second routing skill.
- Reversible on/off changes modify only the managed user rule and installer state.
- Fixed owner manifest to avoid capturing later user-created files in installed Office OS.
