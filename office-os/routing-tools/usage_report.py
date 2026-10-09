#!/usr/bin/env python3
"""Summarize Claude Code JSON/NDJSON result records only. Never persist prompts."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys


def decode_text(raw):
    """Decode UTF-8 (with or without BOM) or UTF-16 (BOM-marked, e.g. PowerShell redirection)."""
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        return raw.decode('utf-16')
    return raw.decode('utf-8-sig')


def read_results(path):
    if path.stat().st_size > 30 * 1024 * 1024:
        raise ValueError('Refusing results file >30 MiB; filter to result records first')
    content = decode_text(path.read_bytes())
    try:
        decoded = json.loads(content)
        items = decoded if isinstance(decoded, list) else [decoded]
    except json.JSONDecodeError:
        items = []
        for number, line in enumerate(content.splitlines(), 1):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                print(f'WARNING: skipped line {number}: not valid JSON', file=sys.stderr)
    return [x for x in items if isinstance(x,dict) and (x.get('type')=='result' or 'modelUsage' in x)]


def _valid(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0


def aggregate(items):
    totals = defaultdict(lambda: {'inputTokens':0, 'outputTokens':0, 'cacheReadInputTokens':0, 'cacheCreationInputTokens':0, 'costUSD':0.0})
    session_cost = 0.0
    sessions = 0
    warnings=[]
    for result in items:
        sessions += 1
        value = result.get('total_cost_usd')
        if _valid(value):
            session_cost += value
        else:
            warnings.append('One result omitted total_cost_usd; cost total may be incomplete')
        models = result.get('modelUsage') or {}
        if not isinstance(models,dict):
            warnings.append('Unexpected modelUsage format; skipped record')
            continue
        for name, record in models.items():
            if not isinstance(record,dict):
                continue
            target=totals[name]
            for field in target:
                number=record.get(field,0)
                if _valid(number):
                    target[field]+=number
                else:
                    warnings.append(f'Invalid {field} for {name}; treated as zero')
    return {'resultCount':sessions,'reportedTotalCostUSD':round(session_cost,6),'models':dict(totals),'warnings':sorted(set(warnings))}


def check_budget(budget):
    if budget is None:
        return None
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget < 0:
        raise ValueError('Budget warning threshold must be a finite, non-negative number')
    return budget


def report(path, record_cfg=None, budget=None):
    budget = check_budget(budget)  # Validate before anything is read or written.
    if not path.is_file():
        raise ValueError('Input results file not found')
    stats = aggregate(read_results(path))
    if not stats['resultCount']:
        print('NO RESULT RECORDS: supply the output of claude -p --output-format json')
        return 1
    print('RESULT RECORDS:',stats['resultCount'])
    print('REPORTED COST USD:',f"${stats['reportedTotalCostUSD']:.4f}", '(not an enforced billing limit)')
    for name,item in sorted(stats['models'].items()):
        print(f"MODEL {name}: input={item['inputTokens']} output={item['outputTokens']} cache_read={item['cacheReadInputTokens']} reported_cost=${item['costUSD']:.4f}")
    if not stats['models']:
        print('WARNING: No per-model usage supplied; cannot verify actual model routing')
    for msg in stats['warnings']:
        print('WARNING:',msg)
    if record_cfg is not None:
        dest=record_cfg/'office-os-routing/usage-history.jsonl'
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('a',encoding='utf-8') as output:
            output.write(json.dumps({'recordedAt':datetime.now(timezone.utc).isoformat(),**stats},sort_keys=True)+'\n')
        print('RECORDED SANITIZED USAGE:',dest)
    if budget is not None:
        if stats['reportedTotalCostUSD']>budget:
            print(f"BUDGET WARNING: reported cost ${stats['reportedTotalCostUSD']:.4f} exceeds ${budget:.4f}. Past usage cannot be prevented by this check.")
            return 2
        print('BUDGET THRESHOLD:',f'${budget:.4f}','not exceeded (reported results only)')
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path)
    ap.add_argument('--budget-usd',type=float)
    ap.add_argument('--record',action='store_true',help='Append sanitized totals to usage-history.jsonl in the config dir')
    ap.add_argument('--config-dir',help='Override CLAUDE_CONFIG_DIR or ~/.claude (used with --record)')
    args=ap.parse_args(argv)
    cfg=None
    if args.record:
        cfg=Path(args.config_dir or os.environ.get('CLAUDE_CONFIG_DIR') or (Path.home()/'.claude')).expanduser().resolve()
    try:
        return report(args.input,cfg,args.budget_usd)
    except (ValueError, OSError) as error:
        print('ERROR:',error,file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
