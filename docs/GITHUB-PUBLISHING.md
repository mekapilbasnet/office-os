# GitHub Publishing Guide

## Suggested repository name

`office-os-dynamic-routing`

## Before pushing

- Review the `LICENSE` file
- Review `SECURITY.md`
- Confirm branding and ownership details
- Confirm whether you want the repository public or private first

## Basic publish steps

```bash
git init
git add .
git commit -m "Initial release: Office OS + Dynamic Routing v4.3"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## Recommended GitHub setup

- Enable GitHub Actions
- Add repository topics such as `claude-code`, `ai-tooling`, `developer-tools`, `automation`
- Add a release tag for your first beta release
