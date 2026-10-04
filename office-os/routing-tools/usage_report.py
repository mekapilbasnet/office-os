#!/usr/bin/env python3
"""Summarize Claude Code JSON/NDJSON result records only. Never persist prompts."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path


def read_results(path):
    if path.stat().st_size > 30 * 1024 * 1024:
        raise ValueError('Refusing results file >30 MiB; filter to result records first')
    content = path.read_text(encoding='utf-8')
    try:
        decoded = json.loads(content)
        items = decoded if isinstance(decoded, list) else [decoded]
    except json.JSONDecodeError:
        items = [json.loads(line) for line in content.splitlines() if line.strip()]
    return [x for x in items if isinstance(x,dict) and (x.get('type')=='result' or 'modelUsage' in x)]


def aggregate(items):
    totals = defaultdict(lambda: {'inputTokens':0, 'outputTokens':0, 'cacheReadInputTokens':0, 'cacheCreationInputTokens':0, 'costUSD':0.0})
    session_cost = 0.0
    sessions = 0
    warnings=[]
    for result in items:
        sessions += 1
        value = result.get('total_cost_usd')
        if isinstance(value,(int,float)) and value>=0:
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
                if isinstance(number,(int,float)) and number>=0:
                    target[field]+=number
                else:
                    warnings.append(f'Invalid {field} for {name}; treated as zero')
    return {'resultCount':sessions,'reportedTotalCostUSD':round(session_cost,6),'models':dict(totals),'warnings':sorted(set(warnings))}


def report(path, record_cfg=None, budget=None):
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
        if budget < 0:
            raise ValueError('Budget warning threshold must be non-negative')
        if stats['reportedTotalCostUSD']>budget:
            print(f"BUDGET WARNING: reported cost ${stats['reportedTotalCostUSD']:.4f} exceeds ${budget:.4f}. Past usage cannot be prevented by this check.")
            return 2
        print('BUDGET THRESHOLD:',f'${budget:.4f}','not exceeded (reported results only)')
    return 0

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path)
    ap.add_argument('--budget-usd',type=float)
    args=ap.parse_args()
    raise SystemExit(report(args.input,budget=args.budget_usd))
