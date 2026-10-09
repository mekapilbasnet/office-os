# Office OS: Model Routing and Observability

> **This is the installer template**, not necessarily what's live. The
> installer (`office-os/routing-tools/routing_manager.py`) derives
> `~/.claude/rules/model-routing.md` from this file. If that live file's
> `ROUTING_STATE` line or body text doesn't match what's here, the installer
> hasn't been (re)applied on that machine — run `/office-os routing diagnose`
> to check, `/office-os routing plan` to preview a sync.

ROUTING_STATE: ON

This policy is loaded automatically and applies to ordinary Claude Code work when enabled; `/office-os` is not required. If it is replaced by the installed OFF rule, do not apply its routing preferences. It picks models only *after* Office OS triage and specialist selection; never skip evidence, authorization, QA or project instructions to save cost.

## Objective

Use the least expensive model that can reliably complete the work, with minimal interruption. Route by capability and task difficulty, not file count.

```text
FAST              -> Haiku
GENERAL           -> Sonnet
DEEP_REASONING    -> Opus
LONG_HORIZON      -> Fable, explicit approval required
```

Prefer model-family aliases over exact version IDs unless pinning is intentional.

## Haiku: discover

Use `Explore` for cheap, read-only discovery: locate files, symbols, schemas, tests and configuration; trace call paths; gather compact context. Not for hard architecture, security-sensitive reasoning, ambiguous root causes, or compatibility decisions.

## Sonnet: build

Sonnet is the normal main and implementation model: features, APIs, ordinary bug fixes, tests, routine refactors, normal database work, documentation, framework-specific implementation, and integrating other agents' findings. Do not spawn a subagent for work Sonnet can do efficiently.

## Opus: reason

Use `deep-reasoner` when the task genuinely needs deeper reasoning:

- unclear root cause, or legacy behavior to reverse-engineer
- non-obvious cross-module interactions, complex business rules
- backward compatibility, architecture tradeoffs
- concurrency, transactions, risky migrations
- auth or other security-sensitive logic, production data risk
- repeated failed attempts, or uncertainty left after Sonnet investigation

Opus investigates and recommends; Sonnet implements afterward. Not for searching, mechanical edits, obvious bugs, formatting, or simple tests.

## Reviewer: check

Use `reviewer` (read-only, Sonnet) for an independent read of a diff, files or a plan before merge or release, or after a risky change (auth, data, migrations, public contracts). It never edits and cannot run tests. Skip it for routine or trivial edits.

## Fable: approval required

NEVER use Fable automatically, as main model, subagent, advisor or fallback. The same applies to any Fable-equivalent, premium long-horizon, maximum-capability autonomous, or unknown-cost premium model.

Before any use: explain briefly why Sonnet/Opus are insufficient, ask for explicit approval, wait for it, and use it only for the current approved task. Approval does not carry between tasks. If denied, continue with Sonnet and/or Opus.

## Mixed tasks and escalation

Delegate only the part that benefits from another model. Typical flow, skipping stages that add nothing: Explore/Haiku discovers, deep-reasoner/Opus reasons (only if needed), Sonnet implements and tests. Escalation order is not required; after deep reasoning, return routine work to Sonnet.

## Advisor and subagents

If an Opus Advisor is already enabled, use it for short decision-point consultation; never enable one just because a task is hard. Prefer `deep-reasoner` for large isolated investigations. Use a subagent only for cheaper exploration, deeper reasoning, context isolation or focused analysis, and avoid redundant or overlapping agents.

## Future models

Classify a new model from official documentation (FAST, GENERAL, DEEP_REASONING, LONG_HORIZON, SPECIALIZED, UNKNOWN), not from its name. LONG_HORIZON and unknown premium models need approval, as with Fable.

## Routing observability and truthful reporting

The status line shows the main session's actual `model.display_name`; the subagent status line shows each agent's **resolved** `model` when Claude Code supplies it. That display is the source of truth, not a model name guessed in prose.

- For substantial delegations, say which agent and model were **requested** and why; label an unknown effective model *requested/unverified*.
- Do not announce the main model for tiny steps.
- If the actual model differs from the intended one, say so and do not claim the plan succeeded. Check `/model`, `/status` and task details; flags, provider mappings, managed/project/local settings and environment overrides can change it.
- If a requested model is unavailable, continue on a permitted model with disclosure, or ask. Never silently fall back to Fable or another premium tier.

## Delegation thresholds

- Skip Explore for trivial, understood edits. Use it when discovery would burn substantial Sonnet context.
- Use deep-reasoner only for material uncertainty, security or data risk, nontrivial architecture, or repeated failures. Codebase size is not difficulty.
- Give subagents scoped goals, files and limits; no overlapping investigations. Require evidence, file paths, uncertainties and verification steps. Treat `maxTurns` hits and incomplete output as **partial**.
- After Opus, use Sonnet for routine changes and tests.
- Instructions alone cannot guarantee manual model choices, fallbacks, managed policy or provider behavior.

## Optional routing profiles

Default is **Balanced**; the ACTIVE profile is in the PROFILE_STATE footer. Change with `/dynamic-routing profile economy|balanced|quality`:

- **Economy:** targeted Haiku discovery; Sonnet for nearly everything else; Opus only after material uncertainty/risk.
- **Balanced:** Haiku for meaningful discovery; Sonnet for implementation and ordinary debugging; Opus for significant complex reasoning.
- **Quality:** Haiku for simple discovery; Sonnet for implementation; Opus sooner for hard, ambiguous reasoning.

These are preferences, not a cost cap or guaranteed model switch.

## Runtime fallbacks

- The installer preserves any existing `fallbackModel` and never adds Fable. Inspect or set it with `/dynamic-routing fallback status|none|sonnet|sonnet-haiku`; it applies to subagents too.
- A fallback is not proof of a good routing choice; check the effective model in the status line or `modelUsage`.
- Profile and fallback changes need a fresh session. `/dynamic-routing usage` summarizes result JSON without storing prompts; costs are estimates, not enforcement.
