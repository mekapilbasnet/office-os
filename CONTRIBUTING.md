# Contributing

Thanks for your interest in improving **Office OS + Dynamic Routing**.

## Development flow

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run tests locally.
5. Open a pull request with a clear summary.

## Local validation

```bash
python3 -m unittest discover -s tests -v
CLAUDE_CONFIG_DIR=$(mktemp -d) ./install.sh --apply   # test in a throwaway config folder
./verify.sh
```

## Contribution guidelines

- Keep changes backward compatible where possible.
- Preserve safety in installation and rollback flows.
- Do not add automatic premium-model fallbacks.
- Document new commands and new routing behavior.
