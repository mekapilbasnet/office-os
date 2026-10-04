# Dynamic Model Routing

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
