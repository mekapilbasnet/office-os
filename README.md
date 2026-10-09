<p align="center">
  <img src="assets/github-header.svg" alt="Office OS with Dynamic Routing" width="100%" />
</p>

<p align="center">
  <strong>One Claude Code skill that picks the right model for each job, so you stop overpaying for easy work.</strong>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-beta-orange">
  <img alt="Tests" src="https://img.shields.io/badge/tests-45%20passed-16a34a">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Claude%20Code-111827">
</p>

## What you get

Install it once. From then on, Claude Code routes work like a sensible manager would:

| Job | Model |
|---|---|
| Find files, trace code | **Haiku** (cheap, fast) |
| Build features, fix bugs, write tests | **Sonnet** (the everyday default) |
| Hard root causes, risky changes, security | **Opus** (only when needed) |
| Independent review of a diff or plan | **Reviewer** agent (read-only, Sonnet) |
| Long autonomous runs | **Fable**, only after you say yes |

You also get:

- `/office-os`: the main skill, for features, bugs, audits and releases that need several disciplines.
- A status line that shows which model is actually running, and what each helper agent is using.
- Simple controls: turn routing on or off, pick a profile (economy, balanced, quality), set fallbacks.
- A safe installer: preview first, backups, and it stops instead of overwriting your own files.

Routing is **on by default** after install. No second skill to set up.

<p align="center">
  <img src="assets/routing-overview.svg" alt="Routing overview" width="100%" />
</p>

<p align="center">
  <img src="assets/status-line-demo.svg" alt="Status line example" width="100%" />
</p>

---

## Install

Needs: Claude Code, Git, and Python 3 (no extra packages).

**Easiest:** paste this into Claude Code.

```
Install the Office OS skill from https://github.com/mekapilbasnet/office-os
— clone it, then run ./install.sh --apply (or install.ps1 --apply on
Windows), then run ./verify.sh (or .\verify.ps1 on Windows).
```

**Or by hand (Linux / macOS / WSL):**

```bash
git clone https://github.com/mekapilbasnet/office-os.git
cd office-os
./install.sh          # preview only
./install.sh --apply  # install
./verify.sh           # check it worked
```

**Windows PowerShell:**

```powershell
git clone https://github.com/mekapilbasnet/office-os.git
Set-Location office-os
.\install.ps1          # preview only
.\install.ps1 --apply  # install
.\verify.ps1           # check it worked
```

Then restart Claude Code and run `/office-os`.

Files go to `~/.claude`. To use another folder, set `CLAUDE_CONFIG_DIR` or pass `--config-dir`. Your main-model setting and custom status line are kept.

## Update

```bash
cd office-os
git pull
./install.sh          # preview the changes
./install.sh --apply  # apply them
./verify.sh
```

Windows: same steps with `.\install.ps1` and `.\verify.ps1`. Restart Claude Code afterwards.

If you edited an installed file, the installer stops and lists the conflicts. Review them before using `--replace`.

Already have standalone Dynamic Routing? Uninstall it first. See [docs/INSTALLATION.md](docs/INSTALLATION.md).

---

## Commands

| Command | What it does |
|---|---|
| `/office-os` | Start the main skill |
| `/dynamic-routing status` | Show whether routing is on |
| `/dynamic-routing on` / `off` | Turn routing on or off |
| `/dynamic-routing profile economy\|balanced\|quality` | Choose cheaper or deeper routing |
| `/dynamic-routing fallback none\|sonnet\|sonnet-haiku` | Set the fallback chain (applies to all subagents; asks first) |
| `/dynamic-routing compatibility` | Check your Claude Code setup |
| `/dynamic-routing usage <path>` | Summarize usage and estimated cost from a Claude Code JSON result |
| `/dynamic-routing history` | Show opt-in usage summaries |
| `/dynamic-routing export` | Save your routing preferences to a file |

Full list: [docs/COMMANDS.md](docs/COMMANDS.md).

---

## Good to know

- Claude Code can override the model you ask for. This project improves routing and visibility but cannot force the model. The status line shows the truth.
- Fable is never used without your approval, for each task.
- A skills check (advisory only) tells you which optional skills the routing guide mentions are installed.

## Optional extras

**Ponytail** is not bundled. Office OS uses it for broad codebase audits and minimal generated code when it is installed:

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

**Design skills** (`brand`, `design`, `ui-ux-pro-max`) live under `skills/`, vendored unmodified from an upstream project. The installer does not install them. See [skills/README.md](skills/README.md) and [skills/THIRD-PARTY-NOTICES.md](skills/THIRD-PARTY-NOTICES.md).

---

## Tests

45 offline tests, installer smoke tests, and CI on Linux, macOS and Windows.

```bash
python3 -m unittest discover -s tests -v
```

On Windows, use `python` or `py`. Static checks do not prove which model Claude Code ran. Live tests are opt-in: see the [smoke test guide](office-os/routing-tools/SMOKE_TESTS.md) and [release checklist](office-os/routing-tools/RELEASE_CHECKLIST.md).

## More docs

[Installation](docs/INSTALLATION.md) · [Commands](docs/COMMANDS.md) · [Architecture](docs/ARCHITECTURE.md) · [Publishing to GitHub](docs/GITHUB-PUBLISHING.md) · [Skill behavior](office-os/SKILL.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
