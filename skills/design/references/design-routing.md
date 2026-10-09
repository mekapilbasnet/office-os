# Design Routing Guide

When to use each design skill. Three skills are installed together: `brand`,
`design` (this one) and `ui-ux-pro-max`. Logo, CIP, slides, banners, icons and
social photos are built into `design`.

## Skill Overview

| Skill | Purpose | Key Files |
|-------|---------|-----------|
| brand | Brand guidelines, voice, assets, token sync | SKILL.md + references + 4 scripts |
| ui-ux-pro-max | Design systems, tokens, UI styling, stack guidance (shadcn, Tailwind, React, ...) | SKILL.md + data + `scripts/search.py` |
| design: logo | AI logo generation (55 styles, 30 palettes) | `references/logo-*.md`, `scripts/logo/` |
| design: CIP | Corporate Identity Program (50 deliverables) | `references/cip-*.md`, `scripts/cip/` |
| design: slides | HTML presentations with Chart.js | `references/slides-*.md` |
| design: banner | Banners for social, ads, web, print (22 styles) | `references/banner-sizes-and-styles.md` |
| design: icon | SVG icon generation (15 styles, Gemini 3.1 Pro) | `references/icon-design.md`, `scripts/icon/` |
| design: social photos | HTML to PNG social images | `references/social-photos-design.md` |

## Routing by Task Type

### Brand Identity Tasks
**-> brand**

- Define brand colors and typography
- Create logo usage guidelines
- Establish brand voice and tone
- Organize and validate assets
- Create messaging frameworks
- Audit brand consistency
- Sync brand guideline colors/fonts into design tokens (`sync-brand-to-tokens.cjs`)

### Token System and Implementation Tasks
**-> ui-ux-pro-max**

- Generate a design system (`--design-system`, optionally `--persist`)
- Pick colors, typography, UX rules, charts, icons
- Stack guidance: `--stack shadcn`, `html-tailwind`, `react`, `nextjs`, ...
- Dark mode, responsive layout, accessible components

### Logo Design Tasks
**-> design (logo)**

- Create logos with AI (Gemini Nano Banana, Atlas Cloud, MuAPI)
- Search logo styles, color palettes, industry guidelines
- Generate design briefs

### Corporate Identity Program Tasks
**-> design (CIP)**

- Generate CIP deliverables (business cards, letterheads, signage, vehicles, apparel)
- Create CIP briefs with industry/style analysis
- Generate mockups with/without logo (Gemini Flash/Pro)
- Render HTML presentations from CIP mockups

### Presentation Tasks
**-> design (slides)**

- Create strategic HTML presentations
- Data visualization with Chart.js
- Apply copywriting formulas to slide content
- Use layout patterns and design tokens

### Banner Design Tasks
**-> design (banner)**

- Social media covers/headers, ad banners, website heroes, print banners
- 22 art direction styles (minimalist, bold typography, gradient, glassmorphism, etc.)

### Icon Design Tasks
**-> design (icon)**

- Generate SVG icons with AI (Gemini 3.1 Pro Preview)
- Batch variations, multi-size export (16, 24, 32, 48 px)
- 15 styles and 12 categories

## Routing by Question Type

| Question | Skill |
|----------|-------|
| "What color should this be?" | brand (if a guideline exists), else ui-ux-pro-max |
| "How do I create a token for X?" | ui-ux-pro-max (`--design-system`), brand (`sync-brand-to-tokens.cjs`) |
| "How do I build a button component?" | ui-ux-pro-max (`--stack shadcn` / your stack) |
| "Is this on-brand?" | brand |
| "How do I add dark mode?" | ui-ux-pro-max |
| "Create a logo for my brand" | design (logo) |
| "Generate business card mockups" | design (CIP) |
| "Create a pitch deck" | design (slides) |
| "What logo style fits my industry?" | design (logo) |
| "Design a Facebook cover / ad banner / hero" | design (banner) |
| "Generate a settings icon / icon set" | design (icon) |

## Multi-Skill Workflows

### New Project Setup

```
1. brand -> Define identity (colors, typography, voice)
2. brand -> sync-brand-to-tokens.cjs to write design-tokens.json / .css
3. ui-ux-pro-max -> --design-system --persist, then --stack <your stack>
```

### Brand Package From Scratch

```
1. design (logo) -> generate logo variants
2. design (CIP)  -> mockups using the chosen logo (--logo)
3. design (slides) -> pitch deck
```

## Quick Commands

**Brand:**
```bash
node ~/.claude/skills/brand/scripts/inject-brand-context.cjs
node ~/.claude/skills/brand/scripts/validate-asset.cjs <path>
node ~/.claude/skills/brand/scripts/sync-brand-to-tokens.cjs
```

**Design system and stack guidance:**
```bash
python ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<product keywords>" --design-system -p "Project"
python ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<keyword>" --stack shadcn
```

## When to Use Multiple Skills

- brand + ui-ux-pro-max: define the design language, then implement it in code
- design (logo) + design (CIP): complete identity package with deliverable mockups
- design (logo + CIP + slides): brand pitch
- design (banner) + brand: on-brand social presence across platforms
