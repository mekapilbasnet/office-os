# Create Slides

Build a persuasive HTML slide deck with design tokens and Chart.js. Everything
needed is in this folder; no extra skill or script is required.

## Workflow

1. **Clarify** the audience, goal, length and any brand guidelines (ask the user
   with `AskUserQuestion` if unclear).
2. **Strategy** - pick a presentation strategy and emotion arc from
   `slides-strategies.md`.
3. **Outline** - one message per slide; write copy with the formulas in
   `slides-copywriting-formulas.md`.
4. **Layout** - choose a pattern per slide from `slides-layout-patterns.md`.
5. **Tokens** - use the project's brand tokens if present (`design-tokens.css`
   from the `brand` skill); otherwise run
   `python ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<topic> <mood>" --design-system`
   and use its colors and fonts.
6. **Build** - start from `slides-html-template.md`; add Chart.js charts for any
   data slide.
7. **Verify** - open the HTML in a browser, step through every slide, check
   contrast and text overflow, then fix and re-check.
