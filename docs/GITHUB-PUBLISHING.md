# GitHub Publishing Guide

## Before you publish

- Review `LICENSE` and `SECURITY.md`
- Confirm the repository name, owner and branding
- Decide whether it starts public or private

## Publish

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## Recommended setup

- Keep GitHub Actions enabled (the workflow runs the tests on Linux, macOS and Windows)
- Add topics such as `claude-code`, `ai-tooling`, `developer-tools`, `automation`
- Tag a release for each version and copy its notes from `CHANGELOG.md`
- Issue and pull request templates and `CODEOWNERS` are already in `.github/`
