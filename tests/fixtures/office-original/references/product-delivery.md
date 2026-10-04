# Product, Design, Architecture, and Delivery Standards

## Discovery and idea validation

Generate opportunities from verified workflow friction, repetitive work, incomplete automation, missing reporting/search/collaboration/notification, accessibility, mobile, integration, data-quality, security, performance, support, analytics, market, or technology evidence.

For serious ideas define the user problem, affected users, evidence, hypothesis, expected outcome, possible solution, simpler alternative, value, complexity, maintenance, risk, operational impact, and success metric.

Challenge the idea:

- Is the problem real and frequent enough?
- Does functionality already exist?
- Can configuration, training, documentation, or process solve it?
- Will users adopt it repeatedly?
- What happens if nothing changes?
- What is the smallest valid experiment?

Decide: Build, Build with conditions, Experiment, Revise, Research, Postpone, Merge, Reject, or Stop.

## Business analysis

For material requirements define only applicable sections:

- measurable business objective;
- actors: users, systems, services, external parties;
- verified current process and proposed process;
- explicit business rules and contradictions;
- permission matrix for view/create/update/delete/approve/reject/export/assign/configure/override;
- required, optional, conditional, format, range, uniqueness, and cross-field validation;
- state model with valid/invalid transitions, allowed actor, side effects, notifications, and audit;
- data fields, owner, source, sensitivity, retention, relationships, and reporting use;
- exceptions: missing/duplicate/unauthorized/inactive/deleted/conflicting/service-failure/partial/cancel/reversal;
- testable acceptance criteria, preferably Given/When/Then where useful;
- explicit out of scope.

Do not hand materially incomplete rules to engineering.

## UX, UI, content, and accessibility

Inspect the current design system, components, routes, roles, responsive behavior, and user journey before designing.

Define:

- user goal and shortest understandable task flow;
- information hierarchy and progressive disclosure;
- permissions and role differences;
- loading, empty, success, validation, error, offline, and partial states;
- destructive-action safeguards and recovery;
- keyboard, focus, semantic, screen-reader, contrast, reflow, motion, and touch behavior;
- clear labels, instructions, errors, confirmation, and status copy;
- responsive layout and data-density behavior.

Reuse established components and tokens unless a verified limitation justifies change. Use specialist design skills as intelligence, not as product truth. Verify significant UI in the rendered interface when tools permit.

## Architecture

Document the existing architecture before proposing a new one. Define only what changes decisions:

- context, constraints, boundaries, and assumptions;
- affected components and data flow;
- interfaces, contracts, versioning, idempotency, timeouts, retry, and failure behavior;
- data model, ownership, lifecycle, migrations, backfill, rollback, and retention;
- auth, authorization, tenancy, audit, secrets, and privacy;
- concurrency, consistency, caching, queues, observability, scalability, and recovery;
- deployment, compatibility, operational ownership, and cost;
- alternatives and why they were not selected;
- failure scenarios and mitigations;
- explicit decision and consequences.

Architecture exists to serve product needs. Avoid prestige abstractions, premature services, or platform change for a local requirement.

## Engineering

### Frontend

Use existing architecture and design system. Keep types, state, validation, permissions, API contracts, errors, loading, accessibility, responsiveness, and tests aligned. Do not use frontend visibility as an authorization boundary.

### Backend

Validate at trust boundaries. Enforce authorization and tenant isolation server-side. Make transaction boundaries, concurrency, idempotency, errors, audit, logging, and external-service failures explicit. Preserve stable contracts or version them deliberately.

### Database

Define constraints, indexes, nullability, defaults, ownership, lifecycle, and data correction. Migrations must consider existing rows, scale, locks, backfill, forward/backward application behavior, rollback or corrective strategy, and verification. Successful execution is not proof of correct data migration.

## Data governance

Identify system of record, owners, sensitivity, allowed use, retention/deletion, quality rules, lineage, access, reporting semantics, reconciliation, and auditability. Validate telemetry quality before using it as evidence.

For migrations require source/target definitions, mapping, transforms, duplicate handling, exception reporting, dry run, reconciliation, backup, cutover, corrective/rollback plan, ownership, and post-migration validation.

## AI/ML delivery

Activate only when the product builds, procures, embeds, or relies on AI/ML.

Define intended/prohibited use, model/provider/version, data categories and provenance, evaluation suite, error/hallucination analysis, prompt-injection defense, sensitive-data handling, human oversight, fallback, latency/cost, monitoring, auditability, misuse risk, and change/retirement controls.

Never claim model safety or reliability without task-relevant evaluation. Treat model/vendor updates as behavior changes that may require regression evaluation.

## Delivery planning

Prefer vertical slices that produce observable value. Include dependencies, sequencing, data and contract changes, test approach, security/privacy requirements, observability, rollout, rollback, documentation, ownership, evidence, and stopping conditions. Keep changes focused and reviewable.
