# Assurance, Security, and Operations

Apply relevant assurance from the start, not only at the end.

## Quality

Build a risk-based strategy from business criticality, frequency, blast radius, data sensitivity, permissions, integrations, and reversibility. Verify positive, negative, boundary, failure, concurrency, compatibility, recovery, and regression paths. Never approve only the happy path.

Use Playwright/API/REST Assured/k6 or equivalent specialist skills only when they fit the existing stack and add distinct coverage.

## Security

Review applicable authentication bypass, broken authorization, privilege escalation, cross-tenant access, injection, XSS, CSRF, SSRF, path traversal, unsafe upload, mass assignment, sensitive-data exposure, weak sessions, token leakage, secrets, enumeration, rate abuse, replay/duplicate processing, redirects, business-logic abuse, dependencies/supply chain, CORS/headers, logging, and insecure defaults.

For findings include title, severity, location, preconditions, evidence, realistic impact, fix, verification, and compensating control where relevant. Do not label a vulnerability without evidence. Security testing must be defensive, authorized, scoped, and non-destructive.

Use an OWASP specialist when installed for high-risk web, API, LLM, or agentic surfaces. It augments, not replaces, system-specific threat modeling.

## Privacy and compliance

Review necessity, purpose limitation, minimization, consent/legal basis when applicable, sensitivity, access, retention/deletion, user rights, logs/analytics, third-party and cross-border processing, AI exposure, incident impact, records, licenses, and auditability.

Identify legal/compliance risk but do not present unqualified interpretation as final legal advice. Escalate material uncertainty.

## Accessibility

Review semantic HTML, keyboard navigation, focus order and visibility, names/labels/descriptions, contrast, touch targets, error/status announcements, screen-reader flow, reduced motion, zoom/reflow, dialogs, forms, and table semantics. Prefer native semantics before ARIA. Use a dedicated accessibility skill for substantial UI when available.

## Performance

Identify user-visible symptom, representative workload, measured baseline, bottleneck, and target before optimizing. Inspect rendering, bundle/network, API latency, database queries/indexes, caching, serialization, queues, concurrency, memory, CPU, storage, and external services. Measure after changes. Use load tests only against authorized targets and safe environments.

## Reliability and platform

Review build repeatability, CI/CD, environment consistency, secrets, containers, capacity, database limits, queues, disk/memory/CPU/connections, logs/metrics/traces, alerts, certificate/credential expiry, backups, tested restore, deployment, rollback, and infrastructure cost.

For critical services define appropriate availability/latency/error targets, RTO, RPO, alerts, owners, runbook, escalation, and manual fallback. A backup is not verified recovery until restored successfully.

## Release and rollback

Ensure steps, configuration, flags, migrations, compatibility, monitoring, alerting, owner, support readiness, rollback trigger, rollback steps, data consequences, and post-release verification are explicit. Do not perform production changes without authorization.

## Vendors and supply chain

For material third parties assess need, alternatives, cost, data exposure, security/privacy/compliance, SLA/support, availability, concentration, contract/license, renewal, portability/export, migration burden, and exit path.

For packages assess provenance, ownership, lock integrity, maintenance, transitive risk, vulnerabilities, license, build/artifact integrity, and whether a dependency is justified. Scan untrusted skills before installation.

## Identity and internal access

Review active and stale users, roles, privileged/service/shared/break-glass accounts, leavers, SSO, MFA, least privilege, access-review cadence, endpoints, SaaS licenses, ownership, and segregation of duties. Never change production access without authorization.

## Business continuity

Map critical processes and services, dependencies, recovery owners, backups/restores, RTO/RPO, vendor outage, alternate operation, key-person risk, and communications. Test recovery rather than relying on documents alone.

## Integration certification

For material integrations define purpose/owner, auth, data contract/version, limits, idempotency, retry/timeout, failure and reconciliation, observability, sandbox/certification, provider SLA/change notice, security/privacy, fallback, and deprecation. Verify the end-to-end path before production activation.

## Assurance decision

Return Passed, Conditional, Failed, Blocked, or Not verified for each material gate. A condition must have an owner, deadline or trigger, and verification path.
