# Architecture Overview

## Layers

1. **Office OS Skill**: main skill entry and cross-functional workflows.
2. **Routing Policy**: decides when routing is on, what profile is active, and how delegation behaves.
3. **Subagents**: Explore (Haiku), implementation path (Sonnet), deep reasoning (Opus), premium path (Fable with approval).
4. **Operational Tooling**: install, verify, diagnose, usage reporting, history, export, uninstall.

## Design intent

- Keep one main skill
- Avoid competing routing skills
- Allow routing to be disabled without removing Office OS
- Preserve user settings wherever possible
