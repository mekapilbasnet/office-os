# Office OS: live model-routing smoke tests

# Opt-in live smoke test (requires your authenticated Claude Code session)

Static validation (`verify`) checks files and settings only. It **cannot** prove that the intended runtime model executed. Run the following tasks manually (or via a user-approved paid test) after restarting Claude Code:

1. Check `/status` or the main status line; it should display the model Claude Code actually reports. User settings alone do not prove the current model because CLI/project/managed overrides can supersede them.
2. Invoke `/office-os` with a medium-size repository discovery task and ask it to delegate a **specific bounded lookup** to `Explore`. In the subagent panel verify the runtime resolved model says Haiku, not just that its definition contains `haiku`.
3. Invoke `/office-os` with a genuinely ambiguous multi-module reasoning task and, if justified, ask it to use `deep-reasoner`. Inspect its effective model and confirm Opus.
4. Ask it to take the findings and perform a trivial implementation. Confirm no unnecessary Opus or redundant Explore delegation.
5. Check Fable is never voluntarily selected without your explicit **per-task** permission. Do not actually invoke Fable to test the prohibition.
6. Temporarily configure a different local main model in a controlled test (or start using an explicit CLI model) and confirm visibility shows the **actual** main model rather than hardcoded Sonnet.
7. Confirm your pre-existing `CLAUDE.md`, custom rules, third-party agents, unrelated `settings.json` fields and status-line customizations remain intact.

Mark each test PASS / FAIL / SKIPPED; record effective model evidence from the UI, not from a model's unsupported self-claim. Model availability and provider-specific aliases may vary. No test is performed automatically by installing the bundle.
