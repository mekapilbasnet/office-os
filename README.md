<p align="center">
  <img src="assets/github-header.svg" alt="Office OS with Dynamic Routing" width="100%" />
</p>

<p align="center">
  <strong>One Claude Code skill that picks the right model for each job, so you stop overpaying for easy work.</strong>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-beta-orange">
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

Needs Claude Code, Git and Python 3.8 or newer (no extra packages).

```bash
git clone https://github.com/mekapilbasnet/office-os.git && cd office-os
./install.sh --apply   # Windows: .\install.ps1 --apply
./verify.sh            # Windows: .\verify.ps1
```

Run `./install.sh` without `--apply` first to preview. Then restart Claude Code and run `/office-os`.

Windows blocked by execution policy? Use `powershell -ExecutionPolicy Bypass -File .\install.ps1 --apply`.

Your main-model setting is kept if you have one. If you have none, the installer sets `model: sonnet`. Your custom status line is kept.

Details, updating, Windows execution policy and conflicts: [docs/INSTALLATION.md](docs/INSTALLATION.md).

---

## Commands

| Command | What it does |
|---|---|
| `/office-os` | Start the main skill |
| `/dynamic-routing status` | Show whether routing is on |
| `/dynamic-routing on` / `off` | Turn routing on or off |
| `/dynamic-routing profile economy\|balanced\|quality` | Choose cheaper or deeper routing |

Everything else (fallbacks, usage, history, export) is in [docs/COMMANDS.md](docs/COMMANDS.md). To roll back or uninstall, see [Manage / Uninstall](docs/COMMANDS.md#manage--uninstall).

---

## Good to know

- Claude Code can override the model you ask for. This project improves routing and visibility but cannot force the model. The status line shows the truth.
- Fable is never used without your approval, for each task.
- A skills check (advisory only) tells you which optional skills the routing guide mentions are installed.

## Optional extras

**Ponytail** and **Caveman** are optional and not bundled. Office OS uses them only if you install them: Ponytail for broad codebase audits, Caveman for token compression and lean build, fix and review skills. Install steps: [docs/INSTALLATION.md](docs/INSTALLATION.md#optional-extras).

**Design skills** (`brand`, `design`, `ui-ux-pro-max`) live under `skills/`, vendored from upstream with local patches (see [skills/THIRD-PARTY-NOTICES.md](skills/THIRD-PARTY-NOTICES.md)). The installer does not install them. See [skills/README.md](skills/README.md).

---

## Tests

Offline tests, installer smoke tests, and CI on Linux, macOS and Windows.

```bash
python3 -m unittest discover -s tests -v
```

On Windows, use `python` or `py`. Static checks do not prove which model Claude Code ran. Live tests are opt-in: see the [smoke test guide](office-os/routing-tools/SMOKE_TESTS.md) and [release checklist](office-os/routing-tools/RELEASE_CHECKLIST.md).

## More docs

[Installation](docs/INSTALLATION.md) · [Commands](docs/COMMANDS.md) · [Architecture](docs/ARCHITECTURE.md) · [Publishing to GitHub](docs/GITHUB-PUBLISHING.md) · [Skill behavior](office-os/SKILL.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)
