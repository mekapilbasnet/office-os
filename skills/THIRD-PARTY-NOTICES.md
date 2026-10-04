# Third-party notices

Everything under `skills/` except this file and `README.md` is vendored from
an upstream project, unmodified except where noted. Office OS itself
(`office-os/`) is original to this repository and not covered here.

## ui-ux-pro-max pack

`brand`, `design`, `ui-ux-pro-max`

| | |
| --- | --- |
| Upstream | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Version | 2.13.0 (commit `08b2e54`) |
| License | MIT — see upstream repository's `LICENSE` |
| Installed | 2026-09-03 |

The upstream pack also ships `banner-design`, `design-system`, `slides`, and
`ui-styling` as standalone skills — dropped from this repo as redundant:
`design` already includes their banner/slide generation, and
`ui-ux-pro-max` already includes design tokens and component styling for
more stacks than `design-system`/`ui-styling` covered. A few of `design`'s
reference files under `skills/design/references/` (slide and banner wording)
originated in those dropped directories; they're kept as plain files now,
not symlinks.

## ui-styling fonts

Removed along with `ui-styling` — this repo no longer ships
`canvas-fonts/`.

## Updating a vendored pack

Don't hand-edit files under a vendored skill directory — re-pull from
upstream instead, so changes don't silently diverge. See `skills/README.md`
for the ui-ux-pro-max pack's update steps.
