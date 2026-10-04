#!/usr/bin/env python3
"""Produce Claude Code per-agent JSON lines using the resolved runtime model."""
import json
import sys


def render(payload):
    rows = []
    for task in payload.get('tasks', []):
        tid = task.get('id')
        if tid is None:
            continue
        name = task.get('name') or task.get('type') or 'Agent'
        model = task.get('model') or 'model unresolved'
        status = task.get('status') or 'unknown'
        desc = (task.get('description') or task.get('label') or '').replace('\n', ' ').strip()
        desc = desc[:65] + ('…' if len(desc) > 65 else '')
        content = f'{name} [{model}] · {status}' + (f' · {desc}' if desc else '')
        rows.append({'id': tid, 'content': content})
    return rows


if __name__ == '__main__':
    try:
        for row in render(json.load(sys.stdin)):
            print(json.dumps(row, ensure_ascii=False))
    except (ValueError, TypeError):
        pass  # Leave default agent rows in place if payload invalid.
