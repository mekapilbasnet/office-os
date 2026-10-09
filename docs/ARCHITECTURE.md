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
├── references/             # workflows, governance, routing guide, templates,
│                           # and model-routing.md (the always-on rule source)
└── routing-tools/
    ├── routing_manager.py  # installer and routing controls
    ├── skills_check.py     # advisory check of which optional skills are installed
    ├── usage_report.py     # usage and cost summary (the usage command)
    ├── manifest.json       # list of files the package owns
    ├── subagents/          # Explore, deep-reasoner, reviewer
    ├── commands/           # /dynamic-routing
    ├── scripts/            # status lines, live smoke test
    ├── OPERATIONS.md       # how an assistant runs the manager
    ├── SMOKE_TESTS.md      # opt-in live test steps
    └── RELEASE_CHECKLIST.md
skills/                     # separate vendored design skills (not installed)
tests/                      # offline regression tests
docs/                       # reference docs
install.* / verify.*        # thin wrappers around routing_manager.py
```

## What an install writes

See [INSTALLATION.md](INSTALLATION.md#what-the-installer-writes-under-claude). Commands are listed in [COMMANDS.md](COMMANDS.md).

## Design intent

- Keep one main skill.
- Avoid competing routing skills.
- Allow routing to be disabled without removing Office OS.
- Preserve user settings wherever possible.
- Never use a premium model without approval.
