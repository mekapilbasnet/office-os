# Third-party notices

Everything under `skills/` except this file and `README.md` is vendored from
upstream projects, unmodified except where noted. Office OS itself
(`office-os/`) is original to this repository and not covered here.

## ui-ux-pro-max pack

`banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling`,
`ui-ux-pro-max`

| | |
| --- | --- |
| Upstream | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Version | 2.13.0 (commit `08b2e54`) |
| License | MIT — see upstream repository's `LICENSE` |
| Installed | 2026-09-03 |

`skills/design/references/` contains symlinks into `skills/slides/` and
`skills/banner-design/` for files the upstream pack ships twice — same
content, single file on disk, both skills still resolve it.

## superset

`superset` (plugin, 13 sub-skills under `skills/superset/skills/`)

| | |
| --- | --- |
| Upstream | https://github.com/superset-sh/superset |
| Homepage | https://docs.superset.sh |
| License | MIT |

## ui-styling fonts

`skills/ui-styling/canvas-fonts/` ships Google Fonts, each under the SIL
Open Font License — see the paired `*-OFL.txt` next to each `.ttf`.

## Updating a vendored pack

Don't hand-edit files under a vendored skill directory — re-pull from
upstream instead, so changes don't silently diverge. See `skills/README.md`
for the ui-ux-pro-max pack's update steps.
