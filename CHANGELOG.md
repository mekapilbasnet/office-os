# v4.3

- Actual persisted Economy/Balanced/Quality routing profiles and guarded rollback.
- Explicitly opt-in safe fallback chains, with warnings that fallback also applies to subagents; reject configured automatic Fable fallback during verification.
- Offline per-model usage/cost reports from user-supplied Claude Code result JSON, optional sanitized history, a portable nonsecret config export, and warning threshold.
- CLI compatibility checker, opt-in paid runtime smoke test, and realistic release checklist.
- Preserved a single Office OS skill and automatic routing on/off behavior.

# Changes

## Office OS + Dynamic Routing v4 integration

- Preserved all original Office OS skill references and agent metadata.
- Added v4 model routing as Office OS reference, not a competing second skill.
- Embedded safe installer/verification/rollback into the Office OS skill's routing tools.
- Installed persistent model policy and read-only Haiku/Opus subagents with observability scripts.
- Added backup-safe upgrade from pristine Office OS + pristine v3 routing files.
- Blocked accidental simultaneous install over a separately managed Dynamic Routing v4 setup.
- Preserved existing main model and custom status lines by default.

## v4.2: automatic activation and toggles

- Automatic model routing ON immediately after installation in new sessions.
- Added `/dynamic-routing off|on|status` control-only command; no second routing skill.
- Reversible on/off changes modify only the managed user rule and installer state.
- Fixed owner manifest to avoid capturing later user-created files in installed Office OS.
