# Evidence and Delivery Contracts

## Evidence labels

Use labels when they improve clarity:

- **Verified:** directly supported by inspected evidence.
- **Implemented:** changed in the current work.
- **Tested:** executed validation supports the claim.
- **Decision:** chosen course and rationale.
- **Recommendation:** proposed next action, not performed.
- **Hypothesis:** testable explanation or expected outcome.
- **Assumption:** unverified input used provisionally.
- **Risk:** plausible negative outcome with impact.
- **Blocked:** cannot proceed within current constraints.
- **Not verified:** no sufficient evidence obtained.
- **Requires approval:** next action exceeds current authorization.

Do not use labels as decoration. Claims remain proportional to evidence.

## Standard task contract

For non-trivial work include only useful fields:

- action-oriented task and measurable objective;
- background and verified problem;
- scope and exclusions;
- responsible/accountable owner or discipline;
- dependencies and affected modules;
- business/implementation notes;
- testable acceptance criteria;
- automated/manual test requirements;
- security, privacy, accessibility, and observability requirements;
- documentation and rollout/rollback;
- evidence-based Definition of Done;
- priority, size, risks, assumptions, and stopping conditions.

Do not create empty template sections.

## Definition of Ready

A significant item is ready when applicable: problem, user, outcome, scope, exclusions, rules, permissions, acceptance, dependencies, UX, architecture/data impact, security/privacy, operational ownership, rollout, and decision authority are sufficiently clear.

Scale readiness to the work. A tiny bug does not need a program charter.

## Definition of Done

Completion may require:

- problem and decision verified;
- business rules, scope, and contracts aligned;
- affected frontend/backend/data/integration layers complete;
- authentication, authorization, tenant isolation, validation, errors, audit, and logging reviewed;
- tests added where they provide value and relevant checks passed;
- migrations, compatibility, deployment, rollback, monitoring, ownership, and documentation handled;
- final diff/status reviewed and unrelated work preserved;
- manual user workflow checked where automation is insufficient;
- a concise verification checklist and QA handover produced when required by project rules or the generic trigger in `workflows.md`;
- remaining risks and unverified areas disclosed;
- measurement plan defined for material product changes.

Do not mark partially verified work complete.

## Command execution and validation

Before running commands, inspect repository scripts and documentation, use the existing package manager, start with focused checks, broaden only as useful, and avoid destructive commands.

Validation may include formatting, lint, type checking, unit/integration/E2E, UI checks, production build, migration validation, dependency/secret scans, diff/status, and searches for debug statements, disabled tests, or placeholders.

When a check fails:

1. read the complete error;
2. determine whether it predates the work;
3. isolate the failure;
4. fix the root cause if in scope;
5. rerun the focused check;
6. rerun the affected broader suite;
7. report unresolved failures accurately.

Never disable tests, remove useful assertions, weaken typing broadly, swallow errors, or add ignores to manufacture a green result.

## Internal challenge

Before substantial completion, ask only relevant questions:

- Does this solve the intended problem and is there a simpler solution?
- Are rules, permissions, states, and exceptions complete?
- Are UX, frontend, backend, data, and contracts aligned?
- Are authorization, tenant isolation, privacy, and data integrity protected?
- Are failures, concurrency, compatibility, and rollback handled?
- Are tests meaningful and evidence current?
- Is the result observable, deployable, supportable, affordable, and owned?
- Will users understand/adopt it and how will success be measured?

Resolve material findings or report them as blockers/risks.

## Final report

Lead with the outcome. Keep the response short enough for the intended reader, use plain language, and include only applicable sections:

1. **Outcome:** delivered result.
2. **Decision:** why the work proceeded, changed, stopped, or was postponed.
3. **Verified evidence / root cause:** decisive facts.
4. **Changes:** product, UX, code, data, security/privacy, operations, analytics, docs.
5. **Validation:** exact checks actually run with Passed, Failed, Blocked, or Not run.
6. **Files changed:** important files and purpose.
7. **Ownership and rollout:** who/what owns it and what must happen next.
8. **Assumptions and remaining risks:** material only.
9. **Manual verification:** concise steps if still required.
10. **QA handover:** location or concise handover when required; do not duplicate its full contents in the final report.
11. **Measurement plan:** for significant product work.
12. **Recommended next action:** one highest-value follow-up when useful.

For code-changing work, include a compact **What to verify** list or table unless the project defines another completion format. Put correctness and risk-critical checks first.

Do not claim a command, test, deployment, metric, review, or visual check occurred unless it did.
