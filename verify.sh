#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found. Install Python 3.8 or newer (https://www.python.org/downloads/) and rerun." >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
  echo "ERROR: Python 3.8 or newer is required (found $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])'))." >&2
  exit 1
fi
exec python3 "${ROOT}/office-os/routing-tools/routing_manager.py" verify "$@"
