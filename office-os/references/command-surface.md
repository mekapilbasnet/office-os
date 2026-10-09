# Office Command Surface

`/office:*` names are a descriptive map, not registered slash commands. Claude Code loads the real skill through `/office-os` (or `$office-os` where supported). If a user types `/office:<name>`, treat it as a request to run that workflow through Office OS, in plain language.

## Workflow commands

`/office:<name> [scope]` is routed as below. Section names refer to headings in the named reference file in this folder.

| Command | Target |
| --- | --- |
| `/office:bootstrap` | workflows.md: Bootstrap |
| `/office:feature`, `/office:bug`, `/office:refactor` | workflows.md: Feature / Bug / Refactor |
| `/office:plan`, `/office:sprint-plan` | workflows.md: Plan or initiative; product-delivery.md: Delivery planning |
| `/office:review` | workflows.md: Review |
| `/office:test` | workflows.md: Test; assurance.md: Quality |
| `/office:release` | workflows.md: Release; assurance.md: Release and rollback |
| `/office:incident` | workflows.md: Incident |
| `/office:measure`, `/office:post-release-review` | workflows.md: Measurement and post-release review |
| `/office:daily`, `/office:eod`, `/office:weekly`, `/office:monthly`, `/office:quarterly` | workflows.md: Operating cadence |
| `/office:status`, `/office:continue` | evidence-delivery.md: Evidence labels, Final report; resume via the matching workflow, inspecting changes first |
| `/office:health`, `/office:org-health` | governance.md: Organizational health |
| `/office:brainstorm`, `/office:verify-idea`, `/office:market-research`, `/office:customer-insights` | product-delivery.md: Discovery and idea validation |
| `/office:support-insights` | governance.md: Conditional functions (voice of customer) |
| `/office:business-analysis` | product-delivery.md: Business analysis |
| `/office:product-review`, `/office:roadmap`, `/office:prioritize` | product-delivery.md: Delivery planning; governance.md: Functional capability map |
| `/office:ui`, `/office:accessibility` | product-delivery.md: UX, UI, content, and accessibility; assurance.md: Accessibility |
| `/office:architecture` | product-delivery.md: Architecture |
| `/office:security` | assurance.md: Security |
| `/office:privacy`, `/office:compliance` | assurance.md: Privacy and compliance |
| `/office:performance` | assurance.md: Performance |
| `/office:ai-review` | product-delivery.md: AI/ML delivery |
| `/office:reliability-review`, `/office:deployment-plan`, `/office:rollback-plan` | assurance.md: Reliability and platform; Release and rollback |
| `/office:continuity-review` | assurance.md: Business continuity |
| `/office:integration-certification` | assurance.md: Integration certification |
| `/office:vendor-review`, `/office:partner-review`, `/office:supply-chain-review` | assurance.md: Vendors and supply chain |
| `/office:access-review` | assurance.md: Identity and internal access |
| `/office:cost-review`, `/office:capacity-review` | governance.md: Functional capability map (finance, delivery) |
| `/office:data-migration` | product-delivery.md: Data governance; governance.md: Conditional functions |
| `/office:service-catalog`, `/office:technology-radar`, `/office:configuration-review`, `/office:entitlement-review`, `/office:automation-review`, `/office:localization-review`, `/office:communications-review`, `/office:privacy-operations`, `/office:lifecycle-review`, `/office:experiment-review`, `/office:process-excellence` | governance.md: Conditional functions |
| `/office:decision-debt`, `/office:policy-exceptions`, `/office:standards-review` | governance.md: Decision rights; Conditional functions |
| `/office:retro` | workflows.md: Operating cadence |
| `/office:technical-debt` | product-delivery.md: Engineering; governance.md: Ownership |

## Model-routing management

Use `/dynamic-routing off|on|status` for direct control. These wrap the Office OS manager and are not a second routing skill. The other rows are subcommands of `/office-os`. Read [routing management operations](../routing-tools/OPERATIONS.md) before running them. The full command list is in the repository's `docs/COMMANDS.md`.

| Command | Route |
| --- | --- |
| `/dynamic-routing off` | Disable the auto-loaded routing rule; preserve visibility and manual model selection |
| `/dynamic-routing on` | Re-enable automatic routing (the default on installation) |
| `/dynamic-routing status` | Show enabled or disabled state without changes |
| `/dynamic-routing profile economy\|balanced\|quality` | Change the active routing profile; needs a fresh session to take full effect |
| `/dynamic-routing fallback status\|none\|sonnet\|sonnet-haiku` | Inspect or opt in to an availability fallback chain (asks first; affects all subagents) |
| `/dynamic-routing usage <result.json>` | Inspect per-model usage reported by Claude Code (not enforcement) |
| `/dynamic-routing history` | Show opt-in sanitized usage summaries |
| `/dynamic-routing export` | Write nonsecret routing preferences to a new file |
| `/dynamic-routing compatibility` | Check the installed Claude CLI version for routing features |
| `/office-os routing plan` | Preview installer changes and configuration conflicts without writing |
| `/office-os routing install` | Inspect preview, request explicit authorization, then apply |
| `/office-os routing verify` | Static checks only; never claim live model execution |
| `/office-os routing diagnose` | Configuration, effective-model limitations and conflict checks |
| `/office-os routing rollback` | Preview and request explicit approval before restore |
| `/office-os routing uninstall` | Restore pre-install routing configuration after approval |
| `/office-os routing smoke-test` | Show the opt-in manual live test checklist (not a manager command) |

## Command output contract

Every command should:

1. state or infer the requested outcome;
2. inspect the evidence required for that command;
3. activate only relevant disciplines and skills;
4. honor approval boundaries;
5. return verified findings or completed work;
6. distinguish assumptions and unverified areas;
7. produce the project's QA handover or the generic Office OS handover when required;
8. avoid empty sections and generic checklists.
