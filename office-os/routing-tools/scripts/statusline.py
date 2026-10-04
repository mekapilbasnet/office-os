#!/usr/bin/env python3
"""Cheap main-session status line: use Claude Code's reported model, never guess."""
import json
import os
import sys
from pathlib import Path


def render(payload):
    model_obj = payload.get('model') or {}
    model = model_obj.get('display_name') or model_obj.get('id') or 'unknown model'
    workspace = payload.get('workspace') or {}
    cwd = workspace.get('current_dir') or payload.get('cwd') or ''
    project = os.path.basename(os.path.normpath(cwd)) if cwd else ''
    context = payload.get('context_window') or {}
    percent = context.get('used_percentage')
    parts = [f'Model: {model}']
    if project:
        parts.append(project)
    if isinstance(percent, (float, int)):
        parts.append(f'context: {percent:.0f}%')
    cost = (payload.get('cost') or {}).get('total_cost_usd')
    if isinstance(cost, (float, int)) and cost >= 0:
        parts.append(f'est. API: ${cost:.2f}')
    # Read only tiny package metadata; never inspect full settings or session prompts.
    cfg = Path(os.environ.get('CLAUDE_CONFIG_DIR') or (Path.home() / '.claude'))
    state_path = cfg / 'office-os-routing/state.json'
    try:
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state.get('enabled', True):
            parts.append('routing: ' + str(state.get('profile', 'balanced')))
        else:
            parts.append('routing: OFF')
    except (OSError, ValueError, TypeError):
        pass
    return ' | '.join(parts)


if __name__ == '__main__':
    try:
        print(render(json.load(sys.stdin)))
    except (ValueError, TypeError):
        print('Model: unknown')
