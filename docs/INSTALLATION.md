# Installation Guide

## Just give Claude the repo URL

Paste into Claude Code:

```
Install the Office OS skill from https://github.com/mekapilbasnet/office-os
— clone it, then run ./install.sh --apply (or install.ps1 --apply on
Windows) and verify.sh.
```

## Linux / macOS / WSL

```bash
./install.sh
./install.sh --apply
./verify.sh
```

## Windows PowerShell

```powershell
.\install.ps1
.\install.ps1 --apply
.\verify.ps1
```

## Notes

- Dynamic Routing is **enabled by default** after installation.
- Restart Claude Code after install or after switching routing on or off.
- Use `/office-os` as the main skill command.
