# Core Workflows

Apply only the workflow needed for the current task.

## Bootstrap

Use for a new or stale workspace.

1. Inspect repository structure, manifests, locks, entry points, frontend/backend boundaries, database/ORM, auth, tenancy, validation, errors, logging, integrations, queues, storage, tests, migrations, containers, CI/CD, deployment, environment templates, documentation, Git state, recent commits, and unfinished work.
2. Create or update `docs/ai-office/project-map.md` with verified facts only.
3. Add only useful product, ownership, workflow, risk, and active-work context. Do not create empty registry files.
4. Report purpose, users, workflows, architecture, data/auth, testing/deployment, ownership gaps, unfinished work, key risks, opportunities, and one highest-value next action.
5. Do not make broad behavior changes during bootstrap unless asked.

## Feature

For a substantial feature:

1. inspect existing implementation and adjacent behavior;
2. verify the user/business problem and whether an existing feature, configuration, training, or smaller change solves it;
3. define owner, outcome, users, scope, exclusions, business rules, permissions, states, validation, data, exceptions, and testable acceptance criteria;
4. challenge value, adoption, maintenance, cost, security, privacy, vendor, and operational assumptions;
5. define UX and architecture only to the depth needed;
6. create a vertical implementation plan across affected layers;
7. implement with migrations, compatibility, observability, and documentation where required;
8. add meaningful automated and manual verification;
9. perform engineering, QA, security/privacy, operations, cost, and adoption review only where material;
10. run validation, inspect final diff/status, prepare rollback/release/measurement, and report evidence.

Skip ceremonial discovery for a small, already-approved, clearly specified feature.

## Bug

1. reproduce or trace the failure;
2. identify affected users, scope, and severity;
3. locate the failing layer and separate symptom from root cause;
4. inspect related changes and comparable paths;
5. add a regression test where practical;
6. apply the smallest correct fix;
7. test the direct path, adjacent behavior, failures, permissions, and data integrity as relevant;
8. review the final diff and report root cause, evidence, limitations, and residual risk.

Do not hide a backend failure with a frontend workaround or broaden the fix without evidence.

## Refactor

Before changing structure:

- identify the maintainability, safety, or measured performance problem;
- establish existing behavior and characterization tests;
- define a narrow scope;
- preserve business behavior and public contracts unless the change is intentional;
- assess migration, deployment, and performance risk.

Refactor in reviewable increments. Stop if behavior cannot be verified or the work becomes an unapproved redesign.

## Plan or initiative

Define problem, sponsor/accountable owner, product owner, technical owner, users, outcome, metrics, scope, exclusions, milestones, dependencies, risks, cost assumptions, vendor dependencies, rollout, rollback, status, and decision log.

Useful statuses: Proposed, Researching, Validating, Approved, Planned, In progress, At risk, Blocked, Released, Measuring, Completed, Stopped.

## Review

Review requirements, business rules, UX, architecture, data integrity, auth, tenant isolation, security, privacy, errors, concurrency, performance, maintainability, tests, migrations, compatibility, operations, cost, and documentation only where applicable.

Use severities: Blocker, High, Medium, Low, Suggestion. For material findings include location, evidence, impact, a realistic failure scenario, recommended fix, and verification.

## Test

Use project tools. Cover relevant:

- unit behavior: calculations, validation, state transitions, permissions, errors, boundaries;
- integration behavior: API/database, transactions, auth, integrations, queues, files, notifications;
- end-to-end critical workflows;
- frontend rendering, interaction, loading, errors, permissions, duplicate submission, and accessibility-critical behavior;
- risks: invalid/missing/extreme input, duplicates, concurrency, expired sessions, wrong roles, cross-tenant access, inactive/deleted records, network/database/provider failure, partial completion, and stale state.

Run focused checks first and broader affected suites after they pass.

## QA handover

Use the project's existing `qa-handover` skill, template, and location when available. Office OS decides whether a handover is needed; the specialist skill owns its exact structure.

Default requirement when the project has no stronger rule:

| Change | QA handover |
| --- | --- |
| Feature or reported bug implemented at ticket, branch, or release-item size | Required |
| User-visible refactor or change to a query, calculation, workflow, or public contract | Required |
| Schema/migration, API contract, authentication, authorization, permission, role, security, or tenant-isolation change | Required |
| UI workflow or accessibility-critical behavior change | Required |
| Internal performance/refactor/configuration change with no observable behavior or contract impact | Use judgment; create one if QA or operations must verify it |
| Tiny isolated edit, documentation/comment-only work, or analysis with no implementation | Normally not required unless project rules say otherwise |

At minimum, make the handover useful to someone who did not implement the change:

- task and affected workflow;
- previous and expected behavior;
- root cause for a defect;
- implementation scope and affected areas;
- setup, test data, roles, or configuration needed;
- positive, negative, permission, edge, and regression scenarios;
- migration, compatibility, deployment, and rollback concerns;
- automated checks actually run and results;
- manual verification still required;
- known limitations, unverified areas, and remaining risks.

Keep it concise and test-oriented. Do not duplicate a project-owned handover format inside Office OS.

## Release

Review product scope/acceptance/metrics; code/contracts/migrations/compatibility; tests/regression/manual evidence; security/privacy; build/configuration/monitoring/backup/rollback; third-party readiness; docs/support/training.

Return one decision:

- **Go**: all applicable gates passed with evidence.
- **Conditional Go**: non-critical conditions are explicit, owned, and time-bound.
- **No-Go**: a critical blocker remains.

Never return Go with unresolved critical security, tenant isolation, data integrity, destructive migration, privacy/compliance, rollback, or production-access risk. Deployment still requires authorization.

## Incident

Priorities:

1. protect users and data;
2. reduce impact and contain;
3. preserve evidence;
4. restore service safely;
5. communicate only verified facts;
6. investigate after stabilization.

Track severity, known times, detection, affected services/users/data, verified timeline, facts, hypotheses, containment, recovery, rollback conditions, communication status, and ownership. Determine root cause only when supported. Produce blameless corrective actions for root cause, contributing factors, and detection gaps.

## Measurement and post-release review

For significant releases define adoption, completion, error, performance, support, business, cost, and guardrail metrics; data-quality checks; observation period; review date; success/failure thresholds; and rollback/removal criteria.

After observation choose: Keep, Improve, Expand, Reduce scope, Roll back, Remove, or Research further.

## Operating cadence

- **Daily:** active work, Git state, build/tests, blockers, incidents, priorities, decisions. Return at most five priorities.
- **End of day:** verified completed work, work in progress, blockers, decisions, validation, risks, next-day priorities.
- **Weekly:** delivery, product/support signals, debt, security, reliability, cost, roadmap, dependencies, capacity, vendors, ownership.
- **Monthly:** outcomes, adoption, customer problems, cost, security/privacy, architecture, quality, debt, organization/access, roadmap, stop/continue/invest decisions.
- **Quarterly:** strategy, market evidence when requested, core workflows, platform/architecture, security/compliance, cost/capacity, vendor concentration, skills/continuity, roadmap decisions.
