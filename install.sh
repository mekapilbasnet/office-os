#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${ROOT}/office-os/routing-tools/routing_manager.py" install "$@"
