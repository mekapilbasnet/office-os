# User-scope Claude Code skills

Available in every project on this machine. Everything here except
`office-os` (repo root) is vendored from an upstream project — see
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for origin, license, and
version of each pack. Don't hand-edit files inside a vendored skill
directory; re-pull from upstream instead, so local edits don't silently
diverge from the source.

## ui-ux-pro-max pack

Three skills kept — `brand`, `design`, `ui-ux-pro-max` — vendored from one
upstream repo. `banner-design`, `design-system`, `slides`, and `ui-styling`
were dropped: `design` already covers banner and slide generation in full,
and `ui-ux-pro-max` already covers design tokens and component styling
across more stacks than `design-system`/`ui-styling` did.

| | |
| --- | --- |
| Upstream | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Version | **2.13.0** (commit `08b2e54`) |
| Installed | 2026-09-03 |
| License | MIT — see the upstream `LICENSE` |

### Updating

```bash
git clone --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill /tmp/uipm
rm -rf ~/.claude/skills/{brand,design,ui-ux-pro-max}
cp -r /tmp/uipm/.claude/skills/{brand,design,ui-ux-pro-max} ~/.claude/skills/
```

`design/references/` has a few files (slide and banner reference docs) that
the upstream pack also ships under its own `slides`/`banner-design`
directories — those aren't installed here, so after an update, diff
`design/references/` against upstream's `slides`/`banner-design` folders by
hand if you want the latest wording.

Then bump the version row above.

### What was audited before install

No `SessionStart`/`PreToolUse` hooks, no credential or env-var access. The only
outbound hosts in the shipped scripts are `fonts.googleapis.com`, `pexels.com` and
`github.com` (font catalogue refresh and stock backgrounds). The `stack/.claude/settings.json`
in the upstream repo is a sample project template and is **not** installed.
