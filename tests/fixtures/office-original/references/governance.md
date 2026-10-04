# Organization and Governance

## Decision rights

### Local reversible

Within scope, ordinary code organization, non-breaking refactors, tests, docs, small UI improvements, naming, and local configuration may proceed without ceremony.

### Cross-team

Shared API contracts, schemas, design-system changes, common libraries, authentication, shared infrastructure, dependencies, and customer workflows require explicit reasoning and affected-owner review.

### High-risk or one-way-door

Destructive data change, irreversible migration, production security/access policy, major vendor or pricing commitment, legal commitment, public communication, or release with known critical risk requires authorized approval.

## Ownership

For significant work identify one accountable product/business owner and one accountable technical owner. Add operational, data, security, support, and vendor owners only when relevant.

For a critical service record purpose, repository, deployment target, dependencies, data, interfaces, monitoring, runbook, backup/recovery, support, and escalation. Avoid orphaned systems.

Use RACI only for genuinely complex cross-functional work. Keep one accountable owner per decision.

## Functional capability map

Activate the smallest relevant set:

- **Executive/strategy:** priorities, investment, major risk acceptance, stop/continue decisions.
- **Product/product operations:** outcomes, roadmap, intake, decisions, adoption, lifecycle.
- **Business analysis:** processes, rules, permissions, states, exceptions, acceptance criteria.
- **Discovery/validation:** user and market evidence, experiments, options, assumption challenge.
- **Program/delivery:** sequencing, dependencies, capacity, risk, status, release coordination.
- **UX/design/accessibility:** journeys, interaction, information, content, design system, inclusion.
- **Architecture/engineering/DX:** system design, implementation, developer productivity, maintainability.
- **Quality/security/privacy/trust:** behavior, abuse, permissions, data protection, risk, controls.
- **Platform/SRE/data/AI:** delivery platform, reliability, observability, analytics, model governance.
- **Legal/risk/audit/finance/procurement:** obligations, controls, cost, vendors, exit strategy.
- **People/internal IT:** skills/capacity, onboarding, access, endpoints, assets, SaaS.
- **Customer/revenue/GTM/support:** onboarding, support insights, billing/entitlements, adoption, truthful messaging.
- **Documentation/change/incident/continuity:** knowledge, training, rollout, response, recovery.

These are review perspectives, not fictional staff.

## Conditional functions

Activate only when their trigger exists:

- partnerships/ecosystem for strategic or implementation partners;
- corporate/crisis communications for significant internal, customer, public, regulatory, or incident messaging;
- localization for multi-language, locale, timezone, currency, RTL, and regional behavior;
- physical security/facilities for offices, hardware, on-premise systems, biometric/POS/network devices;
- process excellence for recurring cross-team operational failure;
- integration governance for material external systems;
- technology radar for version lifecycle and deliberate adopt/trial/assess/hold/deprecate/remove decisions;
- open-source/supply-chain governance for dependency-heavy production systems;
- privacy operations for data-subject requests, consent, processing inventory, retention, and breaches;
- voice of customer for consolidated interviews, surveys, support, churn, and journey evidence;
- feature/API lifecycle for experimental, active, maintenance, deprecated, and retired capabilities;
- configuration/feature-flag governance for production switches and temporary compatibility flags;
- license/subscription/entitlement management for commercial access control;
- automation governance for jobs, queues, bots, imports, reconciliation, and AI workflows;
- decision debt and policy exceptions for temporary compromises requiring review/expiry;
- service catalog for ownership and dependency visibility;
- customer data migration governance for onboarding/system replacement;
- experiment governance for hypothesis, population, metrics, stopping criteria, flags, and cleanup;
- technical standards for organization-wide conventions with owners and explicit exceptions.

## Persistent office memory

Create durable files only when they will be maintained and used. Prefer `docs/ai-office/` and update existing records rather than duplicating them.

Useful records may include project/product/user/process maps, current work, initiative/opportunity/decision registers, architecture decisions, service ownership/catalog, dependencies/vendors/integrations, technology radar, lifecycle/flags/automation/experiments/entitlements, risks/controls/security/privacy/data migrations/AI models/access, quality/release/incidents/metrics/capacity/debt, and an office journal.

Every durable entry should be concise, dated when useful, evidence-linked, owned, and status-aware. Never store credentials, secrets, or unnecessary personal/sensitive data. Do not create empty files just to match a template.

## Escalation triggers

Escalate possible data loss, exposure across tenants, critical authorization or credential failures, suspected compromise, destructive migration, material privacy/legal uncertainty, major unapproved cost, critical vendor without exit, blocked high-impact release, contradictory rules, unknown critical ownership, missing high-risk rollback, inaccessible required functionality, or unbounded AI/model risk.

## Organizational health

Assess unclear ownership, bus factor, capacity and dependency bottlenecks, knowledge silos, handoff failures, support overload, chronic incidents, review/tool friction, duplicated responsibility, and backup/succession. Focus on system design, not unsupported judgments about individuals.
