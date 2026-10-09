#!/usr/bin/env python3
"""Cheap main-session status line: use Claude Code's reported model, never guess."""
import json
import math
import os
import sys
from pathlib import Path


def _dict(value):
    return value if isinstance(value, dict) else {}


def _number(value):
    """Real finite number only: bool, NaN and infinity are not numbers here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:  # int too large to convert to float
        return None


def _text(value):
    return value if isinstance(value, str) and value.strip() else None


def routing_part():
    # Read only tiny package metadata; never inspect full settings or session prompts.
    try:
        cfg = Path(os.environ.get('CLAUDE_CONFIG_DIR') or (Path.home() / '.claude'))
        state = json.loads((cfg / 'office-os-routing/state.json').read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError, RuntimeError):
        return None
    if not isinstance(state, dict):
        return None
    if state.get('enabled', True) is not True:
        return 'routing: OFF'
    profile = state.get('profile')
    return 'routing: ' + (profile if isinstance(profile, str) and profile.strip() else 'balanced')


def render(payload):
    payload = _dict(payload)
    model_obj = _dict(payload.get('model'))
    model = _text(model_obj.get('display_name')) or _text(model_obj.get('id')) or 'unknown model'
    workspace = _dict(payload.get('workspace'))
    cwd = _text(workspace.get('current_dir')) or _text(payload.get('cwd')) or ''
    project = os.path.basename(os.path.normpath(cwd)) if cwd else ''
    percent = _number(_dict(payload.get('context_window')).get('used_percentage'))
    parts = ['Model: ' + model]
    if project:
        parts.append(project)
    if percent is not None:
        parts.append('context: %.0f%%' % percent)
    cost = _number(_dict(payload.get('cost')).get('total_cost_usd'))
    if cost is not None and cost >= 0:
        parts.append('est. API: $%.2f' % cost)
    routing = routing_part()
    if routing:
        parts.append(routing)
    return ' | '.join(parts)


def main():
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass
    try:
        line = render(json.load(sys.stdin))
    except Exception:  # A status line must never fail the host UI.
        line = 'Model: unknown'
    try:
        print(line)
    except Exception:
        print('Model: unknown')
    return 0


if __name__ == '__main__':
    sys.exit(main())
