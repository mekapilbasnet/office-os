# Templates

Use a template only when the work needs that record. Prefer the project's own format when one exists. Fill every field from evidence; write `unknown` rather than guess. Save durable copies under `docs/ai-office/` only when they will be maintained.

## Incident postmortem

- **Summary:** what happened, in two sentences.
- **Impact:** who and what was affected, for how long (verified facts only).
- **Timeline:** dated events with evidence links.
- **Root cause:** the verified cause, separate from contributing factors.
- **What worked / what did not:** detection, response, communication.
- **Actions:** each with owner, due date, and status.
- **Not verified:** open questions.

## Release notes

- **Version / date:**
- **What changed for users:** plain language, one line each.
- **Fixes:**
- **Known issues:**
- **Upgrade or migration steps:**
- **Rollback:** link to the rollback plan.

## Rollback plan

- **Change being released:**
- **Trigger:** the observable signal that means roll back.
- **Decision owner:** who may call it.
- **Steps:** ordered, each reversible or marked irreversible.
- **Data impact:** what is lost or must be restored; backup location.
- **Verification:** how to confirm the rollback worked.
- **Communication:** who is told, and when.

## Decision record

- **Decision:** one sentence.
- **Date / owner:**
- **Context:** the problem and constraints.
- **Options considered:** with the reason each was kept or dropped.
- **Consequences:** risks accepted and follow-up work.
- **Status:** proposed, accepted, superseded.
