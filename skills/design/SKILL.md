---
name: design
description: "Comprehensive design skill: logo generation (55 styles, Gemini, Atlas Cloud, or MuAPI AI), corporate identity program (50 deliverables, CIP mockups), HTML presentations (Chart.js), banner design (22 styles, social/ads/web/print), icon design (15 styles, SVG, Gemini 3.1 Pro), social photos (HTML→screenshot, multi-platform). Brand guidelines live in the `brand` skill; design tokens and UI styling in `ui-ux-pro-max`. Actions: design logo, create CIP, generate mockups, build slides, design banner, generate icon, create social photos, social media images. Platforms: Facebook, Twitter, LinkedIn, YouTube, Instagram, Pinterest, TikTok, Threads, Google Ads."
argument-hint: "[design-type] [context]"
license: MIT
metadata:
  author: claudekit
  version: "2.1.0"
---

# Design

Unified design skill: logo, CIP, slides, banners, social photos, icons. Brand guidelines are handled by the `brand` skill and design tokens / UI styling by `ui-ux-pro-max` (both installed alongside this skill).

## When to Use

- Logo design and AI generation
- Corporate identity program (CIP) deliverables
- Presentations and pitch decks
- Banner design for social media, ads, web, print
- Social photos for Instagram, Facebook, LinkedIn, Twitter, Pinterest, TikTok

## Sub-skill Routing

| Task | Sub-skill | Details |
|------|-----------|---------|
| Brand identity, voice, assets | `brand` | Separate skill (installed alongside) |
| Design tokens, CSS vars, UI styling (shadcn/ui, Tailwind) | `ui-ux-pro-max` | Separate skill: `--design-system`, `--stack shadcn` / `html-tailwind` |
| Logo creation, AI generation | Logo (built-in) | `references/logo-design.md` |
| CIP mockups, deliverables | CIP (built-in) | `references/cip-design.md` |
| Presentations, pitch decks | Slides (built-in) | `references/slides.md` |
| Banners, covers, headers | Banner (built-in) | `references/banner-sizes-and-styles.md` |
| Social media images/photos | Social Photos (built-in) | `references/social-photos-design.md` |
| SVG icons, icon sets | Icon (built-in) | `references/icon-design.md` |

## Logo Design (Built-in)

55+ styles, 30 color palettes, 25 industry guides. Gemini Nano Banana, Atlas
Cloud, and MuAPI image generation.

### Logo: Generate Design Brief

```bash
python3 ~/.claude/skills/design/scripts/logo/search.py "tech startup modern" --design-brief -p "BrandName"
```

### Logo: Search Styles/Colors/Industries

```bash
python3 ~/.claude/skills/design/scripts/logo/search.py "minimalist clean" --domain style
python3 ~/.claude/skills/design/scripts/logo/search.py "tech professional" --domain color
python3 ~/.claude/skills/design/scripts/logo/search.py "healthcare medical" --domain industry
```

### Logo: Generate with AI

**ALWAYS** generate output logo images on a plain white background (the generator's prompt template asks for this too).

```bash
python3 ~/.claude/skills/design/scripts/logo/generate.py --brand "TechFlow" --style minimalist --industry tech
python3 ~/.claude/skills/design/scripts/logo/generate.py --prompt "coffee shop vintage badge" --style vintage
python3 ~/.claude/skills/design/scripts/logo/generate.py --brand "TechFlow" --provider atlas
python3 ~/.claude/skills/design/scripts/logo/generate.py --brand "TechFlow" --provider muapi
python3 ~/.claude/skills/design/scripts/logo/generate.py --brand "TechFlow" --provider muapi --muapi-model nano-banana-pro
```

**IMPORTANT:** When scripts fail, try to fix them directly.

After generation, **ALWAYS** ask user about HTML preview via `AskUserQuestion`. If yes, invoke `/ui-ux-pro-max` for gallery.

## CIP Design (Built-in)

50+ deliverables, 20 styles, 20 industries. Gemini Nano Banana (Flash/Pro).

### CIP: Generate Brief

```bash
python3 ~/.claude/skills/design/scripts/cip/search.py "tech startup" --cip-brief -b "BrandName"
```

### CIP: Search Domains

```bash
python3 ~/.claude/skills/design/scripts/cip/search.py "business card letterhead" --domain deliverable
python3 ~/.claude/skills/design/scripts/cip/search.py "luxury premium elegant" --domain style
python3 ~/.claude/skills/design/scripts/cip/search.py "hospitality hotel" --domain industry
python3 ~/.claude/skills/design/scripts/cip/search.py "office reception" --domain mockup
```

### CIP: Generate Mockups

```bash
# With logo (RECOMMENDED)
python3 ~/.claude/skills/design/scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --deliverable "business card" --industry "consulting"

# Full CIP set
python3 ~/.claude/skills/design/scripts/cip/generate.py --brand "TopGroup" --logo /path/to/logo.png --industry "consulting" --set

# Pro model (4K text)
python3 ~/.claude/skills/design/scripts/cip/generate.py --brand "TopGroup" --logo logo.png --deliverable "business card" --model pro

# Without logo
python3 ~/.claude/skills/design/scripts/cip/generate.py --brand "TechFlow" --deliverable "business card" --no-logo-prompt
```

Models: `flash` (default, `gemini-2.5-flash-image`), `pro` (`gemini-3-pro-image-preview`)

### CIP: Render HTML Presentation

```bash
python3 ~/.claude/skills/design/scripts/cip/render-html.py --brand "TopGroup" --industry "consulting" --images /path/to/cip-output
```

**Tip:** If no logo exists, use Logo Design section above first.

## Slides (Built-in)

Strategic HTML presentations with Chart.js, design tokens, copywriting formulas.

Load `references/slides-create.md` for the creation workflow.

### Slides: Knowledge Base

| Topic | File |
|-------|------|
| Creation Guide | `references/slides-create.md` |
| Layout Patterns | `references/slides-layout-patterns.md` |
| HTML Template | `references/slides-html-template.md` |
| Copywriting | `references/slides-copywriting-formulas.md` |
| Strategies | `references/slides-strategies.md` |

## Banner Design (Built-in)

22 art direction styles across social, ads, web, print. Uses `ui-ux-pro-max` for style research, the built-in logo/icon generators (or images the user supplies) for visuals, and headless Chrome / Playwright for PNG export.

Load `references/banner-sizes-and-styles.md` for complete sizes and styles reference.

### Banner: Workflow

1. **Gather requirements** via `AskUserQuestion` — purpose, platform, content, brand, style, quantity
2. **Research** — Activate `ui-ux-pro-max` (style, color, typography searches); ask the user for reference links if they have any
3. **Design** — Create HTML/CSS banner (use `frontend-design` too if it is installed); use user-supplied images, or generate marks/icons with the scripts in this skill
4. **Export** — Screenshot to PNG at exact dimensions with headless Chrome or Playwright (see `references/social-photos-design.md`)
5. **Present** — Show all options side-by-side, iterate on feedback

### Banner: Quick Size Reference

| Platform | Type | Size (px) |
|----------|------|-----------|
| Facebook | Cover | 820 x 312 |
| Twitter/X | Header | 1500 x 500 |
| LinkedIn | Personal | 1584 x 396 |
| YouTube | Channel art | 2560 x 1440 |
| Instagram | Story | 1080 x 1920 |
| Instagram | Post | 1080 x 1080 |
| Google Ads | Med Rectangle | 300 x 250 |
| Website | Hero | 1920 x 600-1080 |

### Banner: Top Art Styles

| Style | Best For |
|-------|----------|
| Minimalist | SaaS, tech |
| Bold Typography | Announcements |
| Gradient | Modern brands |
| Photo-Based | Lifestyle, e-com |
| Geometric | Tech, fintech |
| Glassmorphism | SaaS, apps |
| Neon/Cyberpunk | Gaming, events |

### Banner: Design Rules

- Safe zones: critical content in central 70-80%
- One CTA per banner, bottom-right, min 44px height
- Max 2 fonts, min 16px body, ≥32px headline
- Text under 20% for ads (Meta penalizes)
- Print: 300 DPI, CMYK, 3-5mm bleed

## Icon Design (Built-in)

15 styles, 12 categories. Gemini 3.1 Pro Preview generates SVG text output.

### Icon: Generate Single Icon

```bash
python3 ~/.claude/skills/design/scripts/icon/generate.py --prompt "settings gear" --style outlined
python3 ~/.claude/skills/design/scripts/icon/generate.py --prompt "shopping cart" --style filled --color "#6366F1"
python3 ~/.claude/skills/design/scripts/icon/generate.py --name "dashboard" --category navigation --style duotone
```

### Icon: Generate Batch Variations

```bash
python3 ~/.claude/skills/design/scripts/icon/generate.py --prompt "cloud upload" --batch 4 --output-dir ./icons
```

### Icon: Multi-size Export

```bash
python3 ~/.claude/skills/design/scripts/icon/generate.py --prompt "user profile" --sizes "16,24,32,48" --output-dir ./icons
```

The icon is generated once and rescaled for each size (one API call total).

### Icon: Top Styles

| Style | Best For |
|-------|----------|
| outlined | UI interfaces, web apps |
| filled | Mobile apps, nav bars |
| duotone | Marketing, landing pages |
| rounded | Friendly apps, health |
| sharp | Tech, fintech, enterprise |
| flat | Material design, Google-style |
| gradient | Modern brands, SaaS |

**Model:** `gemini-3.1-pro-preview` — text-only output (SVG is XML text). No image generation API needed.

## Social Photos (Built-in)

Multi-platform social image design: HTML/CSS → screenshot export. Uses the `ui-ux-pro-max` and `brand` skills plus headless Chrome / Playwright for export.

Load `references/social-photos-design.md` for sizes, templates, best practices.

### Social Photos: Workflow

1. **Plan** — Break the work into a short checklist (one item per concept x size); run independent items in parallel subagents if available
2. **Analyze** — Parse prompt: subject, platforms, style, brand context, content elements
3. **Ideate** — 3-5 concepts, present via `AskUserQuestion`
4. **Design** — Read the project's brand guidelines (`brand` skill) and run `ui-ux-pro-max` (`--design-system`) for tokens, layout and hierarchy; build HTML per idea × size
5. **Export** — Headless Chrome or Playwright screenshot at exact px (2x deviceScaleFactor)
6. **Verify** — Open each exported PNG (or use a browser tool if available) to inspect it; fix layout/styling issues and re-export
7. **Report** — Short summary of design decisions (save to the project's reports/docs folder if it has one)
8. **Organize** — Put outputs in a clearly named folder per campaign/platform

### Social Photos: Key Sizes

| Platform | Size (px) | Platform | Size (px) |
|----------|-----------|----------|-----------|
| IG Post | 1080×1080 | FB Post | 1200×630 |
| IG Story | 1080×1920 | X Post | 1200×675 |
| IG Carousel | 1080×1350 | LinkedIn | 1200×627 |
| YT Thumb | 1280×720 | Pinterest | 1000×1500 |

## Workflows

### Complete Brand Package

1. **Logo** → `scripts/logo/generate.py` → Generate logo variants
2. **CIP** → `scripts/cip/generate.py --logo ...` → Create deliverable mockups
3. **Presentation** → Load `references/slides-create.md` → Build pitch deck

### New Design System

1. **Brand** (`brand` skill) → Define colors, typography, voice; run `node ~/.claude/skills/brand/scripts/sync-brand-to-tokens.cjs` to produce `design-tokens.json` / `design-tokens.css`
2. **Tokens + styling** (`ui-ux-pro-max` skill) → `search.py "<product keywords>" --design-system --persist -p "Project"` for a persisted Master design system, then `--stack shadcn` / `html-tailwind` for Tailwind and component guidance

## References

| Topic | File |
|-------|------|
| Design Routing | `references/design-routing.md` |
| Logo Design Guide | `references/logo-design.md` |
| Logo Styles | `references/logo-style-guide.md` |
| Logo Colors | `references/logo-color-psychology.md` |
| Logo Prompts | `references/logo-prompt-engineering.md` |
| CIP Design Guide | `references/cip-design.md` |
| CIP Deliverables | `references/cip-deliverable-guide.md` |
| CIP Styles | `references/cip-style-guide.md` |
| CIP Prompts | `references/cip-prompt-engineering.md` |
| Slides Create | `references/slides-create.md` |
| Slides Layouts | `references/slides-layout-patterns.md` |
| Slides Template | `references/slides-html-template.md` |
| Slides Copy | `references/slides-copywriting-formulas.md` |
| Slides Strategy | `references/slides-strategies.md` |
| Banner Sizes & Styles | `references/banner-sizes-and-styles.md` |
| Social Photos Guide | `references/social-photos-design.md` |
| Icon Design Guide | `references/icon-design.md` |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/logo/search.py` | Search logo styles, colors, industries |
| `scripts/logo/generate.py` | Generate logos with Gemini AI |
| `scripts/logo/core.py` | BM25 search engine for logo data |
| `scripts/cip/search.py` | Search CIP deliverables, styles, industries |
| `scripts/cip/generate.py` | Generate CIP mockups with Gemini |
| `scripts/cip/render-html.py` | Render HTML presentation from CIP mockups |
| `scripts/cip/core.py` | BM25 search engine for CIP data |
| `scripts/icon/generate.py` | Generate SVG icons with Gemini 3.1 Pro |
| `scripts/_common.py` | Shared BM25 search + `.env` key loader used by the logo, CIP and icon scripts |

## Prerequisites

**Python:** This skill uses Python scripts. Commands use the full path `~/.claude/skills/design/scripts/...`, so the working directory does not matter. On Windows, use `python` instead of `python3`, and in cmd/PowerShell use `%USERPROFILE%\.claude\skills\design\scripts\...` / `$HOME\.claude\skills\design\scripts\...` since `~` may not expand.

Check if Python is installed:
```bash
python3 --version || python --version
```

## Setup

```bash
export GEMINI_API_KEY="your-key"  # https://aistudio.google.com/apikey
pip install google-genai pillow

# Optional providers for logo generation (no extra Python package required)
export ATLASCLOUD_API_KEY="your-key"   # --provider atlas
export MUAPI_API_KEY="your-key"        # --provider muapi
```

The scripts read only `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ATLASCLOUD_API_KEY` and `MUAPI_API_KEY`, either from the environment or from a `KEY=value` line in `design/.env`, `~/.claude/skills/.env` or `~/.claude/.env` (other lines in those files are ignored).

MuAPI uses the asynchronous model endpoint and prediction result API. See the
[MuAPI API reference](https://muapi.ai/docs/api-reference) for authentication
and the [nano-banana model contract](https://api.muapi.ai/api/v1/models/nano-banana)
or [nano-banana-pro model contract](https://api.muapi.ai/api/v1/models/nano-banana-pro)
for the current model-specific schemas. The logo generator supports both documented
model slugs and sends their shared required `prompt` plus optional `aspect_ratio`
fields; the Pro model also accepts an optional `resolution` field that this focused
logo workflow leaves at the provider default.

> **Note for Windows:** Use `python` instead of `pip` where needed (e.g., `python -m pip install ...`).

## Integration

**Sibling skills (installed alongside):** `brand` (guidelines, asset checks, token sync), `ui-ux-pro-max` (design systems, tokens, UI styling, stack guidance)
**Optional:** `frontend-design` (if installed)
