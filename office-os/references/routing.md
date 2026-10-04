# Routing and Skill Selection

Use this reference after intake classification. Select the minimum useful path and prefer installed specialist skills over reimplementing their methods.

## Discover local instructions first

Before choosing a workflow or specialist, identify the repository and path-specific instructions that govern the target files. Use their commands, test tools, artifact formats, and completion gates instead of inventing generic substitutes. Treat conflicting, stale, or foreign-project instructions as an explicit issue to resolve, not as silent precedent.

## Risk and depth

Treat work as higher risk when it affects authentication, authorization, tenant isolation, money, payroll, billing, regulated or sensitive data, data deletion, migrations, production infrastructure, integrations, public APIs, external communication, AI decisions, or large user populations.

| Level | Typical work | Review depth |
| --- | --- | --- |
| Low | Copy change, narrow docs, local reversible code edit | One discipline, focused check |
| Moderate | Normal bug, feature, UI flow, refactor | Product/engineering plus relevant QA |
| High | Auth, money, migration, sensitive data, platform, public contract | Cross-functional review, rollback, broader validation |
| Critical | Incident, active exposure, destructive or irreversible change | Containment/escalation, explicit approval, independent evidence where possible |

## Default engineering stack

Use these roles when the named skills are installed. Absence of a named skill is not a blocker; perform the underlying work directly using project tools.

| Need | Default | Conditional addition | Boundary |
| --- | --- | --- | --- |
| Investigation | `investigate-first` | `caveman-explore` for Caveman flow; `ponytail-audit` for a broad legacy audit | Do not run all three by default |
| Product ambiguity | `brainstorming` | Office OS discovery and red-team review | Skip when approved requirements are already clear |
| Planning | `writing-plans` | `sparc-methodology` only for genuinely large multi-agent programs | Plan in proportion to task size |
| Implementation | Caveman: `surgical-patch`, `lean-build`, `safe-refactor`, or `migration` | `executing-plans` for a prepared plan | Caveman is the default build/fix layer |
| Debugging | `systematic-debugging` | `bugs`, `qa-handover` for defect artifacts | Find root cause before patching |
| Testing | `test-driven-development` where it improves design or prevents regression | Playwright/API and k6 skills for E2E/performance | Use the repository's existing tools first |
| QA handover | Project `qa-handover` skill or template | Office OS generic handover from `workflows.md` | Use project format when one exists; do not duplicate it |
| Code review | `code-review` | `security-review`, `verification-quality`, `ponytail-review` for distinct specialist questions | Avoid duplicate general reviews |
| Verification | `verification-before-completion` | `caveman-evidence-review` or `verify-and-stop` in Caveman mode | Never claim success without executed evidence |
| Branch/release | `finishing-a-development-branch` | GitHub skills when remote repository action is requested | Do not push, merge, or release without authorization |

## Caveman and Ponytail

- Use **Caveman by default** for building, fixing, refactoring, migration work, and evidence-driven completion.
- Use **Ponytail conditionally** for broad codebase audits, technical-debt analysis, maintainability trends, or improvement discovery across a messy or legacy area.
- For debt-heavy work, Ponytail may inspect first, then Caveman implements the selected changes.
- Do not chain both on routine work.

## Specialist routing

| Task signal | Useful skills when installed |
| --- | --- |
| UI/UX | `ui-ux-pro-max`, `design-system`, `frontend-design`, `ui-styling`; add accessibility specialist for meaningful UI |
| Accessibility | `accessibility-agents` or equivalent WCAG/assistive-technology skill |
| Security | `security-review`; add OWASP specialist for auth, APIs, uploads, sensitive data, dependencies, or AI/agent surfaces |
| QA automation | Playwright/E2E/API test specialist; REST Assured for Java API suites where it matches the repo |
| Performance | k6/load-test skill plus repository profiling tools |
| Documents | docs/docx/pdf/pptx/xlsx specialist matching the requested artifact |
| GitHub | GitHub code review, project, workflow, release, or multi-repo skill matching the exact remote action |
| AI product | AI evaluation/governance skill; Langfuse only when the product actually uses it |
| Agent observability | OpenLIT or AI Observer, not both initially |
| Skill supply-chain safety | SkillSpector or equivalent before installing untrusted third-party skills |

Treat third-party skills as code. Review their instructions, hooks, shell commands, dependencies, network behavior, permissions, and licensing before installation. Do not grant broad permissions merely because a catalog lists a skill.

## Multi-agent routing

Use `subagent-driven-development`, `dispatching-parallel-agents`, Claude-Flow, swarm, or similar only when:

- at least two scopes are independent;
- parallel execution reduces time or improves independent review;
- ownership boundaries and merge strategy are clear;
- workers can access the required evidence;
- central synthesis will resolve conflicts.

Keep sequential work in one agent. Do not use a swarm for a small fix, one dependent chain, or as theater.

## Common routes

### Bug

`investigate-first` → `systematic-debugging` → regression test → `surgical-patch` → focused/broader tests → review → verification → QA handover when required

### Feature

Inspect → verify problem → business analysis/UX/architecture as needed → `writing-plans` → `lean-build` or `executing-plans` → tests → review → verification → QA handover → release/measurement plan

### Refactor

Verify current behavior → characterization tests → `safe-refactor` → compatibility/performance checks → review → verification

### Debt-heavy legacy area

`ponytail-audit` or `ponytail-debt` → prioritize evidence-backed items → Caveman implementation → verification

### UI redesign

Inspect existing design system and flows → product/UX definition → UI specialist → accessibility review → frontend implementation → visual/interaction validation

### Database change

Inspect schema/data/contracts → migration plan → compatibility and rollback/backfill strategy → `migration` → integrity/concurrency tests → operational review

### High-risk review

Office OS framing → focused code/security/privacy/data/operations reviewers → reconcile findings by severity → evidence-based decision

## Conflict resolution

When skills disagree, apply this order:

1. user intent and authorization;
2. verified product and repository evidence;
3. security, privacy, data integrity, and legal constraints;
4. explicit business rules and public contracts;
5. project conventions and maintainability;
6. specialist preference.

Record material unresolved conflicts as risks or blockers instead of averaging them away.

## Model routing (after workflow/specialist selection)

Only when `ROUTING_STATE: ON` is present in the active user rule, for Claude Code execution consult [model-routing.md](model-routing.md) after identifying the smallest justified workflow and specialty. Prefer direct Sonnet work when delegation offers no clear benefit; use bounded `Explore`/Haiku for meaningful discovery and `deep-reasoner`/Opus for genuinely difficult investigations. Distinguish the **requested** model from the **effective** model shown by runtime status. Do not use an approval-only premium model without task-specific authorization. See the core Office OS skill for routing-management commands.
