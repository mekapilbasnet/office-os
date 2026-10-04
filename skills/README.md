# User-scope Claude Code skills

Available in every project on this machine.

## ui-ux-pro-max pack

Seven skills — `banner-design`, `brand`, `design`, `design-system`, `slides`,
`ui-styling`, `ui-ux-pro-max` — vendored from one upstream repo.

| | |
| --- | --- |
| Upstream | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Version | **2.13.0** (commit `08b2e54`) |
| Installed | 2026-09-03 |
| License | MIT — see the upstream `LICENSE` |

Installed by copying the repo's `.claude/skills/*` here, which is what
`uipro init --ai claude --global` does. The alternative routes are
`/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill` (updatable through
Claude Code) or `npm i -g ui-ux-pro-max-cli`.

### Updating

```bash
git clone --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill /tmp/uipm
rm -rf ~/.claude/skills/{banner-design,brand,design,design-system,slides,ui-styling,ui-ux-pro-max}
cp -r /tmp/uipm/.claude/skills/* ~/.claude/skills/
```

Then bump the version row above.

### What was audited before install

No `SessionStart`/`PreToolUse` hooks, no credential or env-var access. The only
outbound hosts in the shipped scripts are `fonts.googleapis.com`, `pexels.com` and
`github.com` (font catalogue refresh and stock backgrounds). The `stack/.claude/settings.json`
in the upstream repo is a sample project template and is **not** installed.
