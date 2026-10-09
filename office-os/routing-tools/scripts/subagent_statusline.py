#!/usr/bin/env python3
"""Produce Claude Code per-agent JSON lines using the resolved runtime model."""
import json
import sys


def _str(value, default=''):
    if value is None or isinstance(value, (bool, dict, list)):
        return default
    text = str(value).strip()
    return text or default


def render(payload):
    rows = []
    tasks = payload.get('tasks') if isinstance(payload, dict) else None
    if not isinstance(tasks, list):
        return rows
    for task in tasks:
        try:
            if not isinstance(task, dict):
                continue
            tid = task.get('id')
            if tid is None or isinstance(tid, (bool, dict, list)):
                continue
            name = _str(task.get('name')) or _str(task.get('type')) or 'Agent'
            model = _str(task.get('model'), 'model unresolved')
            status = _str(task.get('status'), 'unknown')
            desc = (_str(task.get('description')) or _str(task.get('label'))).replace('\n', ' ').strip()
            desc = desc[:65] + ('…' if len(desc) > 65 else '')
            content = f'{name} [{model}] · {status}' + (f' · {desc}' if desc else '')
            rows.append({'id': tid, 'content': content})
        except Exception:
            continue  # One malformed task must not hide the others.
    return rows


def main():
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass
    try:
        rows = render(json.load(sys.stdin))
    except Exception:
        return 0  # Leave default agent rows in place if payload invalid.
    for row in rows:
        try:
            print(json.dumps(row, ensure_ascii=False))
        except Exception:
            try:
                print(json.dumps(row))
            except Exception:
                continue
    return 0


if __name__ == '__main__':
    sys.exit(main())
