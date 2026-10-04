# Office OS: Model Routing and Observability

> **This is the installer template**, not necessarily what's live. The
> installer (`office-os/routing-tools/routing_manager.py`) derives
> `~/.claude/rules/model-routing.md` from this file. If that live file's
> `ROUTING_STATE` line or body text doesn't match what's here, the installer
> hasn't been (re)applied on that machine — run `/office-os routing diagnose`
> to check, `/office-os routing plan` to preview a sync.

ROUTING_STATE: ON

This automatically loaded policy applies to ordinary Claude Code work when enabled; explicit `/office-os` invocation is not required. If the rule is replaced by the installed OFF rule, do not apply its model-routing preferences.

This reference is integrated into the **Office OS** skill. It selects execution models only *after* Office OS triage and domain/specialist selection. Do not skip Office OS evidence, authorization, QA or user/project instruction requirements to optimize model cost. The persistent copy installed at `~/.claude/rules/model-routing.md` makes model defaults available beyond explicit skill invocation. For activation use `/dynamic-routing off`, `/dynamic-routing on`, or `/dynamic-routing status`. Office OS remains the only full orchestration skill; `/dynamic-routing` is only a lightweight command.


## Objective

Use the least expensive model that can reliably complete the current work while preserving correctness and minimizing unnecessary interruption.

Route by capability and task difficulty, not by file count.

Current mapping:

```text
FAST              -> Haiku
GENERAL           -> Sonnet
DEEP_REASONING    -> Opus
LONG_HORIZON      -> Fable, explicit approval required
```

Prefer model-family aliases rather than exact version IDs unless version pinning is intentional.

## Haiku: discover

Use `Explore` for cheap, read-only repository discovery:

- locate files, symbols, endpoints, entities, schemas, tests, and configuration
- trace references and call paths
- identify where a feature is implemented
- gather compact context before deeper reasoning

Do not use Haiku for difficult architecture, security-sensitive reasoning, ambiguous root-cause analysis, or backward-compatibility decisions.

## Sonnet: build

Sonnet is the normal main model and implementation model.

Use it for:

- ordinary features
- CRUD and APIs
- normal bug fixes
- DTOs and validation
- tests
- routine refactors
- normal database work
- documentation
- Java/Spring and Node/NestJS implementation
- integrating findings returned by other agents

Do not create a subagent for work Sonnet can handle efficiently itself.

## Opus: reason

Use `deep-reasoner` when the task genuinely requires deeper reasoning, such as:

- unclear root cause
- legacy behavior that must be reverse-engineered
- non-obvious cross-module interactions
- complex business rules
- important backward compatibility
- architecture tradeoffs
- concurrency or transaction reasoning
- risky migrations
- authentication/authorization or security-sensitive logic
- production data risk
- repeated failed attempts
- unresolved uncertainty after normal Sonnet investigation

Opus should normally investigate and recommend.

Sonnet should normally implement afterward.

Do not use Opus for simple searching, mechanical edits, obvious bugs, formatting, or straightforward tests.

## Fable: approval required

NEVER use Fable automatically.

Before any Fable use:

1. explain briefly why Sonnet/Opus are insufficient or why Fable adds material value
2. ask the user for explicit approval
3. wait for approval
4. use Fable only for the current approved task

Approval does not carry between tasks.

If approval is denied, continue with Sonnet and/or Opus.

Apply the same rule to future Fable-equivalent, premium long-horizon, maximum-capability autonomous, or unknown-cost premium models.

## Mixed tasks

Delegate only the portion that benefits from another model.

Typical flow:

```text
Explore/Haiku -> discover
deep-reasoner/Opus -> reason, only if needed
Sonnet -> implement and test
```

Skip stages that do not add value.

## Escalation

Conceptual escalation:

```text
Haiku -> Sonnet -> Opus -> Fable
```

This is not a required sequence.

After deep reasoning is complete, de-escalate routine work back to Sonnet.

## Advisor-aware behavior

If an Opus Advisor is already enabled, it may be used for short decision-point consultation where full-conversation context is useful.

Do not enable an advisor automatically just because a task is difficult.

Prefer `deep-reasoner` for substantial isolated investigation that would otherwise flood the main context.

Never use or configure a Fable Advisor without the same explicit approval required for direct Fable use.

## Subagent discipline

Use a subagent when it gives meaningful benefit:

- lower-cost exploration
- deeper reasoning
- context isolation
- focused specialist analysis

Avoid redundant agents and overlapping investigations.

## Future models

When a new model appears, classify it from official documentation as:

```text
FAST
GENERAL
DEEP_REASONING
LONG_HORIZON
SPECIALIZED
UNKNOWN
```

Then map it to the capability role.

Do not infer capability from the model name alone.

LONG_HORIZON and unknown premium models require approval.

## Final principle

Optimize for:

```text
correctness
+ sufficient reasoning
+ low unnecessary cost
+ minimal interruption
```

## Routing observability and truthful reporting (v4)

The installed status line reports the main session's actual `model.display_name`, while the installed subagent status line reports each agent's actual **resolved** `model` when supplied by Claude Code. The display is the source of truth, not a model name guessed in prose.

- For substantial delegations, briefly say which agent and model were **requested** and why. If an effective model isn't known, label the model *requested/unverified*.
- Never repeatedly announce the main model for every tiny step. Use the terminal status line as the default display.
- When the actual subagent model differs from the intended model, state the difference and avoid claiming the routing plan succeeded.
- Inspect `/model`, `/status` and active task details when a mismatch is suspected. CLI flags, provider mappings, managed/project/local settings and environment overrides can alter the result.
- If a requested model is unavailable, either continue locally on an appropriate permitted model with disclosure or request guidance. Never silently fall back to approval-only Fable or another premium tier.

## Task thresholds, bounded delegation and handoffs (v4)

- Skip separate Explore runs for trivial, already-understood edits. Start a focused Explore task when discovery would otherwise consume substantial Sonnet context.
- Escalate to deep-reasoner only for material uncertainty, security or data risk, nontrivial architectural decisions, or repeated failed attempts. Do not equate codebase size with difficulty.
- Give subagents scoped goals, relevant files and limits. Do not run overlapping investigations without a concrete reason.
- Require evidence-backed findings, file paths, uncertainties and concrete verification suggestions. Treat `maxTurns` and incomplete outputs as **partial**, not confirmed conclusions.
- After Opus investigation, use Sonnet for routine changes and testing unless actual implementation complexity justifies otherwise.
- No skill or instruction-only setup can guarantee enforcement of every future manual model selection, built-in fallback, managed policy or provider behavior.

## Optional routing profiles (v4)

Installed default is **Balanced**. The ACTIVE installed profile is specified in the appended PROFILE_STATE footer. Change with `/dynamic-routing profile economy|balanced|quality`:

- **Economy:** targeted Haiku discovery; Sonnet handles almost all implementation and initial reasoning; Opus only after material uncertainty/risk.
- **Balanced:** Haiku for meaningful discovery; Sonnet for implementation and ordinary debugging; Opus for significant complex reasoning.
- **Quality:** Haiku for simple discovery; Sonnet for implementation; escalate difficult ambiguous reasoning to Opus sooner.

All profiles require explicit task-specific approval for Fable. These are *instructional preferences*, not a technical cost cap or guaranteed model switch.


## Runtime fallbacks and observability

- Default installer behavior preserves the existing `fallbackModel` setting; it never injects Fable. Use `/dynamic-routing fallback status|none|sonnet|sonnet-haiku` to inspect or explicitly configure. Claude Code applies fallback chains to subagents as well.
- A fallback model is not automatically evidence of a successful routing choice. Inspect effective model in the subagent status line or `modelUsage` of a live JSON result.
- Each fallback or routing profile change requires a fresh Claude Code session to reliably refresh persistent instructions.
- `/dynamic-routing usage` summarizes user-supplied result JSON without storing prompt text. Costs are Claude Code's reported estimates, not billing enforcement.
