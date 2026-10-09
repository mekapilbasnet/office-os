# User-scope Claude Code skills

Available in every project on this machine. Everything here except
`office-os` (repo root) is vendored from an upstream project and then
**locally patched** — see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) for
origin, license, version, and the full "Local patches" list. Because the files
are no longer identical to upstream, a re-pull overwrites the patches: after
updating, re-apply or drop them as described there.

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

Then re-apply the local patches listed in `THIRD-PARTY-NOTICES.md` (diff your
copy against the old one first) and bump the version row above.

### What the scripts do (audited)

No `SessionStart`/`PreToolUse` hooks. The scripts are plain Python/Node with no
network access except where noted:

- **Environment / keys.** The `design` generators read `GEMINI_API_KEY`,
  `GOOGLE_API_KEY`, `ATLASCLOUD_API_KEY` and `MUAPI_API_KEY` from the
  environment, and from `KEY=value` lines in `design/.env`,
  `~/.claude/skills/.env` and `~/.claude/.env`. Only those four names are
  loaded from those files; every other line is ignored. Keys are sent only to
  the matching provider.
- **Outbound hosts.** The Gemini API (`generativelanguage.googleapis.com`, via
  the `google-genai` package) for logo, CIP and icon generation; `api.atlascloud.ai`
  and `api.muapi.ai` for the optional logo providers (generated images are
  downloaded from the HTTPS URL the provider returns, without credentials).
  The data-refresh tooling in `ui-ux-pro-max` is not vendored, so the font and
  icon catalogues are never fetched at run time.
- **Local files.** Scripts write only to the output paths you pass (or the
  current directory / `assets/` for the brand sync).

The `stack/.claude/settings.json` in the upstream repo is a sample project
template and is **not** installed.
