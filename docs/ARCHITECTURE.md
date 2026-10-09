# Architecture Overview

## Layers

1. **Office OS skill**: the main entry point (`/office-os`) and its cross-functional workflows.
2. **Routing policy**: a global rule that says when routing is on, which profile is active, and how work is delegated.
3. **Subagents**:
   - `Explore` (Haiku): read-only discovery
   - `deep-reasoner` (Opus): read-only deep investigation
   - `reviewer` (Sonnet): read-only review of a diff, files or a plan
   - Sonnet does the building itself; Fable only with per-task approval
4. **Operational tooling**: install, verify, diagnose, usage reporting, history, export, rollback, uninstall.

## Repository layout

```text
office-os/                  # the package that gets installed as one skill
├── SKILL.md                # skill entry point
├── agents/openai.yaml      # skill metadata (OpenAI-style interface file)
├── references/             # workflows, governance, routing guide, templates
└── routing-tools/
    ├── routing_manager.py  # installer and routing controls
    ├── manifest.json       # list of files the package owns
    ├── subagents/          # Explore, deep-reasoner, reviewer
    ├── commands/           # /dynamic-routing
    └── scripts/            # status lines, live smoke test
skills/                     # separate vendored design skills (not installed)
tests/                      # offline regression tests
docs/                       # reference docs
install.* / verify.*        # thin wrappers around routing_manager.py
```

## What an install writes (under `~/.claude`)

- `skills/office-os/`: the skill and its routing tools
- `rules/model-routing.md`: the routing rule (swapped for an OFF rule when disabled)
- `agents/`: the three subagents
- `commands/dynamic-routing.md`: the control command
- Status line settings, only if you have none
- A backup folder and install state, so changes can be rolled back

## Design intent

- Keep one main skill.
- Avoid competing routing skills.
- Allow routing to be disabled without removing Office OS.
- Preserve user settings wherever possible.
- Never use a premium model without approval.
