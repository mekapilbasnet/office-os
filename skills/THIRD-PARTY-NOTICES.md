# Third-party notices

Everything under `skills/` except this file and `README.md` is vendored from
an upstream project and then **locally patched** (see "Local patches" below).
Office OS itself (`office-os/`) is original to this repository and not covered
here.

## ui-ux-pro-max pack

`brand`, `design`, `ui-ux-pro-max`

| | |
| --- | --- |
| Upstream | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| Version | 2.13.0 (commit `08b2e54`) |
| License | MIT (full text below) |
| Installed | 2026-09-03 |

The upstream pack also ships `banner-design`, `design-system`, `slides`, and
`ui-styling` as standalone skills — dropped from this repo as redundant:
`design` already includes their banner/slide generation, and
`ui-ux-pro-max` already includes design tokens and component styling for
more stacks than `design-system`/`ui-styling` covered. A few of `design`'s
reference files under `skills/design/references/` (slide and banner wording)
originated in those dropped directories; they're kept as plain files now,
not symlinks.

### License (MIT)

```
MIT License

Copyright (c) 2024 Next Level Builder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

(Copyright line and text taken from the upstream `LICENSE` file at
https://raw.githubusercontent.com/nextlevelbuilder/ui-ux-pro-max-skill/main/LICENSE.)

## Bundled data

### Phosphor Icons (MIT)

`ui-ux-pro-max/data/icons.csv` and `ui-ux-pro-max/data/phosphor-icons-upstream.json`
contain icon names/metadata from Phosphor Icons
(https://github.com/phosphor-icons/core, catalog 2.1.1).

```
MIT License

Copyright (c) 2023 Phosphor Icons

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Google Fonts metadata

`ui-ux-pro-max/data/google-fonts.csv` and `ui-ux-pro-max/data/google-font-licenses.json`
list font family names and metadata taken from the Google Fonts repository
(https://github.com/google/fonts, revision `038b637da7b3fd956a4ed93ffc607c3d5e4ce172`).
No font files are bundled. Each family keeps its own license, recorded per
family in `google-font-licenses.json`: SIL Open Font License 1.1 (OFL), Apache
License 2.0 (APACHE2) or Ubuntu Font License (UFL). If you use a font in a
product, check that family's license in the Google Fonts repository.

## ui-styling fonts

Removed along with `ui-styling` — this repo no longer ships
`canvas-fonts/`.

## Local patches

The project owner approved patching the vendored files, so they are **no
longer byte-identical to upstream**. A re-pull from upstream (see
`skills/README.md`) overwrites these patches; re-apply or re-port them
afterwards. Every patched, added or removed file is listed here.

### ui-ux-pro-max

- `ui-ux-pro-max/SKILL.md` — commands use `~/.claude/skills/ui-ux-pro-max/scripts/search.py` instead of the unset `${CLAUDE_PLUGIN_ROOT}`; removed reference to a missing README and the empty "Workflow" heading; Windows note for `~` paths.
- `ui-ux-pro-max/scripts/design_system.py` — `safe_slug` keeps Unicode letters/digits/marks (hash fallback instead of one shared `default`); `_write_persisted_file` falls back to exclusive create when hard links are unavailable.
- `ui-ux-pro-max/scripts/tests/test_safe_slug.py` — added.
- Removed (they import upstream-only scripts that are not vendored): `scripts/tests/test_catalog_refresh.py`, `test_catalog_summary_line_endings.py`, `test_relevance_evaluator.py`, and their now-unused fixtures `scripts/tests/fixtures/` (catalog and relevance fixtures).

### design

- `design/SKILL.md` (script commands use full `~/.claude/skills/design/scripts/...` paths plus a Windows note), `design/references/design-routing.md`, `slides-create.md`, `slides-strategies.md`, `slides-copywriting-formulas.md`, `slides-layout-patterns.md`, `slides-html-template.md`, `social-photos-design.md` — removed references to skills/scripts that are not installed (`design-system`, `ui-styling`, `ai-artist`, `ai-multimodal`, `chrome-devtools`, `project-management`, `assets-organizing`, `search-slides.py`, `generate-tokens.cjs`); redirected to `brand` / `ui-ux-pro-max`; added `ATLASCLOUD_API_KEY` to setup; logo background rule made consistent.
- `design/scripts/_common.py` — new: shared BM25 search (keeps 2-character tokens, caches CSV and index) and a `.env` loader limited to `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ATLASCLOUD_API_KEY`, `MUAPI_API_KEY`.
- `design/scripts/logo/core.py`, `design/scripts/cip/core.py` — use `_common.py`; `cip/core.py` parses "Key Deliverables" correctly (ignores generic adjectives such as "premium" in fuzzy matching; "vehicle" maps to Van).
- `design/scripts/logo/generate.py` — MuAPI poll URL pinned to `api.muapi.ai`, API key only sent to provider hosts and stripped on cross-host redirects; `--batch` without `--brand` works; lettermark uses the brand's first letter; `--industry` honoured; non-zero exit on failure; prompt template asks for a white background.
- `design/scripts/logo/tests/test_generate.py` — extra tests.
- `design/scripts/cip/generate.py` — `--mockup` honoured with `--set`; logo loaded once; non-zero exit on failure.
- `design/scripts/cip/render-html.py` — HTML-escaped output, whole-word deliverable matching, no `loading="lazy"` on data URIs.
- `design/scripts/icon/generate.py` — `apply_viewbox_size` only edits the root `<svg>` tag; SVG sanitiser (XML-parsing allow/deny; rejects malformed or DOCTYPE SVG, drops on* attributes, script/foreignObject/style imports, SMIL href animation, unsafe `href`/`xlink:href`); `--color` validated; `--sizes` generates once and rescales; Gemini SDK imported lazily; non-zero exit on failure.
- `design/scripts/tests/` — new unit tests (`test_common.py`, `test_icon.py`, `test_cip.py`, `_loader.py`).

### brand

- `brand/SKILL.md`, `brand/references/update.md`, `brand/references/approval-checklist.md` — truthful script descriptions, `~/.claude/skills/...` paths, inline `review` / `create` guidance, no pointers to missing skills.
- `brand/scripts/sync-brand-to-tokens.cjs` — generates `design-tokens.css` itself (no `design-system` script), creates `assets/` when missing, takes the brand name from the guideline title instead of a hard-coded one, starts from the bundled starter tokens when the project has none.
- `brand/templates/design-tokens-starter.json` — added; recovered from the earlier vendored `design-system/templates/design-tokens-starter.json` of the same upstream pack.
- `brand/scripts/extract-colors.cjs` — real colour extraction for SVG and 8-bit PNG (no external tool), clean error for `--brand-file` without a value, no pointer to the missing `ai-multimodal` skill.
- `brand/scripts/validate-asset.cjs` — implements the dimension check (PNG/JPEG/GIF/WebP header parsing, SVG width/height/viewBox); dropped the unimplemented `--fix` claim.
- `brand/scripts/tests/test_sync_brand_to_tokens.py` — converted from pytest to `unittest`, uses the in-skill starter tokens, skips without `node`; extra tests for the other brand scripts.

## Updating a vendored pack

Re-pull from upstream with the steps in `skills/README.md`, then re-apply the
local patches above (or drop the ones upstream has since fixed).
