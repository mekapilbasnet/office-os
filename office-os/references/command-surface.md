# Office Command Surface

Slash commands are thin entry points into Office OS. Each inherits the core skill and adds only its specialized workflow. If the host does not support namespaced commands, invoke `$office-os` with the same command name and arguments in plain language.

## Organization

| Command | Route |
| --- | --- |
| `/office:bootstrap` | Workspace inspection and project map |
| `/office:daily`, `/office:eod`, `/office:weekly`, `/office:monthly`, `/office:quarterly` | Operating cadence in `workflows.md` |
| `/office:health`, `/office:org-health` | Organizational and system health |
| `/office:status` | Verified state, progress, blockers, risks, next action |
| `/office:continue` | Resume existing verified plan/work; inspect changes before acting |

## Product and business

| Command | Route |
| --- | --- |
| `/office:brainstorm` | Evidence-based opportunity discovery and challenge |
| `/office:verify-idea [idea]` | Problem/value/feasibility/risk/experiment decision |
| `/office:product-review` | Outcome, workflow, adoption, lifecycle, roadmap review |
| `/office:business-analysis [requirement]` | Rules, permissions, states, data, exceptions, acceptance |
| `/office:roadmap`, `/office:prioritize` | Outcomes, evidence, dependencies, capacity, risk, priority |
| `/office:customer-insights`, `/office:support-insights` | Consolidate evidence without inventing sentiment |
| `/office:market-research [question]` | Current external evidence with source attribution when browsing is authorized |

## Design and engineering

| Command | Route |
| --- | --- |
| `/office:ui [scope]` | Product/UX/UI/accessibility/frontend workflow |
| `/office:accessibility [scope]` | Accessibility assurance |
| `/office:feature [description]` | Feature workflow |
| `/office:bug [details]` | Bug workflow |
| `/office:refactor [scope]` | Behavior-preserving refactor workflow |
| `/office:architecture [requirement]` | Architecture decision |
| `/office:plan [initiative]`, `/office:sprint-plan` | Delivery plan and sequencing |

## Quality, security, privacy, data, and AI

| Command | Route |
| --- | --- |
| `/office:review [scope]` | Risk-prioritized code/product review |
| `/office:test [scope]` | Risk-based test strategy and execution |
| `/office:security [scope]` | Authorized defensive security review |
| `/office:privacy [scope]`, `/office:compliance [scope]` | Privacy/compliance risk analysis |
| `/office:performance [scope]` | Measure, diagnose, improve, remeasure |
| `/office:ai-review [scope]` | AI intent, data, evaluation, safety, cost, fallback |

## Operations and reliability

| Command | Route |
| --- | --- |
| `/office:release` | Go, Conditional Go, or No-Go decision |
| `/office:incident [details]` | Containment, recovery, evidence, investigation |
| `/office:reliability-review` | SLOs, failure/recovery, ownership, observability |
| `/office:continuity-review` | Critical processes, RTO/RPO, restore, alternatives |
| `/office:deployment-plan` | Authorized, observable, reversible deployment plan |
| `/office:rollback-plan` | Trigger, steps, data/config effects, verification |

## Business operations and governance

| Command | Route |
| --- | --- |
| `/office:cost-review`, `/office:capacity-review` | Cost, consumption, forecast, capacity, trade-offs |
| `/office:vendor-review [vendor]` | Need, risk, cost, SLA, portability, exit |
| `/office:partner-review [partner or integration]` | Shared ownership, data, SLA, support, fallback |
| `/office:access-review [scope]` | Identity, privilege, leavers, services, MFA/SSO |
| `/office:service-catalog [scope]` | Purpose, ownership, dependencies, operation, lifecycle |
| `/office:technology-radar` | Adopt/Trial/Assess/Hold/Deprecate/Remove |
| `/office:supply-chain-review [scope]` | Dependencies, provenance, vulnerability, license, build integrity |
| `/office:configuration-review [scope]` | Flags/settings/env ownership, default, expiry, cleanup |
| `/office:entitlement-review [scope]` | Contract/billing/backend/frontend/limit alignment |
| `/office:automation-review [scope]` | Trigger, inputs, idempotency, retry, observability, fallback |
| `/office:data-migration [scope]` | Map, transform, dry run, reconcile, cutover, verify |
| `/office:localization-review [scope]` | Locale, language, time, currency, format, RTL, validation |
| `/office:communications-review [scope]` | Verified facts, audience, timing, approvals, corrections |
| `/office:privacy-operations [scope]` | Requests, consent, inventory, retention, subprocessors, breach |
| `/office:lifecycle-review [item]` | Proposal through retirement/deprecation |
| `/office:experiment-review [experiment]` | Hypothesis, assignment, metrics, stopping, cleanup |
| `/office:decision-debt` | Temporary decisions, owner, impact, revisit/expiry |
| `/office:policy-exceptions` | Requirement, risk, approval, control, expiry, remediation |
| `/office:standards-review` | Evidence-based cross-org standards and exceptions |
| `/office:process-excellence` | Rework, cycle time, handoffs, repeat failures |
| `/office:integration-certification [integration]` | Contract, reliability, reconciliation, security, end-to-end evidence |

## Improvement

| Command | Route |
| --- | --- |
| `/office:retro` | Evidence, outcomes, friction, causes, actions, owners |
| `/office:technical-debt` | Debt inventory, impact, evidence, priority, remediation |
| `/office:measure [feature]`, `/office:post-release-review [feature]` | Outcome measurement and keep/improve/expand/reduce/rollback/remove decision |

## Integrated model-routing management

| Command | Route |
| --- | --- |
| `/dynamic-routing off` | Disable the auto-loaded routing rule; preserve visibility and manual model selection |
| `/dynamic-routing on` | Re-enable automatic routing (the default on installation) |
| `/dynamic-routing status` | Show enabled/disabled state without changes |
| `/office-os routing plan` | Preview installer changes and configuration conflicts without writing |
| `/office-os routing install` | Inspect preview, request explicit authorization, then apply |
| `/office-os routing verify` | Static checks only; never claim live model execution |
| `/office-os routing diagnose` | Configuration, effective-model limitations and conflict checks |
| `/office-os routing rollback` | Preview and request explicit approval before restore |
| `/office-os routing uninstall` | Restore pre-install routing configuration after approval |
| `/office-os routing smoke-test` | Show opt-in manual live session test checklist |

Use `/dynamic-routing off`, `/dynamic-routing on`, or `/dynamic-routing status` for direct control. These legacy slash commands wrap the Office OS manager; they are not a second routing skill. The other management commands below are subcommands of **Office OS**. Claude Code loads the real skill via `/office-os` (or `$office-os` in an environment supporting that syntax); `/office:*` is a descriptive command surface unless separately registered. Read [routing management operations](../routing-tools/OPERATIONS.md) before running commands.

## Command output contract

Every command should:

1. state or infer the requested outcome;
2. inspect the evidence required for that command;
3. activate only relevant disciplines/skills;
4. honor approval boundaries;
5. return verified findings or completed work;
6. distinguish assumptions and unverified areas;
7. produce the project's QA handover or the generic Office OS handover when required;
8. avoid empty sections and generic checklists.

- `/dynamic-routing profile economy|balanced|quality`: change the active routing profile, with state backup and fresh-session requirement.
- `/dynamic-routing fallback status|none|sonnet|sonnet-haiku`: inspect or opt in to an availability fallback chain.
- `/dynamic-routing usage <result.json>`: inspect actual per-model usage reported by Claude Code (not enforcement).
- `/dynamic-routing compatibility`: verify installed Claude CLI version for supported routing features.
