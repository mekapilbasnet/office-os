# Contributing

Thanks for your interest in improving **Office OS + Dynamic Routing**.

## Development flow

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run tests locally.
5. Open a pull request with a clear summary.

## Local validation

Use Python 3.8 or newer.

```bash
python3 -m unittest discover -s tests -v

# Try the installer in a throwaway config folder, never your real ~/.claude
export CLAUDE_CONFIG_DIR=$(mktemp -d)
./install.sh --apply
./verify.sh
unset CLAUDE_CONFIG_DIR
```

## Contribution guidelines

- Keep changes backward compatible where possible.
- Preserve safety in installation and rollback flows.
- Do not add automatic premium-model fallbacks.
- Document new commands and new routing behavior.
