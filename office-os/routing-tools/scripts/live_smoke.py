#!/usr/bin/env python3
"""Opt-in authenticated Claude Code smoke test. Records only model IDs/usage, not prompts."""
import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASKS = [
    ('main','Reply exactly: ROUTING-SMOKE-MAIN. Do not delegate.', 'sonnet',False),
    ('explore','Use the available Explore subagent once to find a file named routing_smoke.txt in this folder and report its first line. Do not edit any file.', 'haiku',True),
    ('reason','Use the deep-reasoner subagent once to assess the tradeoff between caching and fresh reads for the test note. Do not edit files.', 'opus',True),
]

def family(name):
    n = name.lower()
    for alias in ('fable','haiku','sonnet','opus'):
        if alias in n:
            return alias
    return 'unknown'

def parse_output(text):
    """Return (result_dict_or_None, all_records). Accepts one object, a JSON array, or NDJSON."""
    try:
        decoded = json.loads(text)
        records = decoded if isinstance(decoded, list) else [decoded]
    except (ValueError, TypeError):
        records = []
        for line in (text or '').splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    records = [r for r in records if isinstance(r, dict)]
    results = [r for r in records if r.get('type') == 'result']
    if results:
        return results[-1], records
    if len(records) == 1 and 'modelUsage' in records[0]:
        return records[0], records
    return None, records

def delegation_tool_uses(records):
    """Count Task/Agent tool_use blocks, or None when the output has no message records to inspect."""
    seen = False
    count = 0
    for record in records:
        message = record.get('message')
        content = message.get('content') if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        seen = True
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('name') in ('Task', 'Agent'):
                count += 1
    return count if seen else None

def token_total(usage):
    if not isinstance(usage, dict):
        return 0
    total = 0
    # Cache read/creation tokens are excluded: the main model's cached context would dominate the share.
    for field in ('inputTokens', 'outputTokens'):
        value = usage.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                if math.isfinite(value) and value > 0:
                    total += value
            except OverflowError:
                continue
    return total

def finite_or_none(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:
        return None

def run(cli, cwd, out=None, timeout=180):
    resolved = shutil.which(cli) or (cli if Path(cli).is_file() else None)
    if resolved is None:
        raise RuntimeError('Claude CLI not found. Install it and sign in first.')
    record=[]
    for tag, prompt, expected, delegation in TASKS:
        # stream-json (+ --verbose) emits per-message records, so Task/Agent tool_use blocks are visible.
        cmd=[resolved,'-p',prompt,'--output-format','stream-json','--verbose','--max-turns','5', '--allowedTools','Read,Glob,Grep,Agent']
        # Do not pin the model: this probes the actual default and loaded routing.
        # Existing user/managed overrides may therefore produce an honest mismatch.
        try:
            result=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,check=False)
        except subprocess.TimeoutExpired:
            record.append({'test':tag,'status':'INCONCLUSIVE','reason':'timed out'})
            continue
        data, records = parse_output(result.stdout or '')
        if data is None:
            record.append({'test':tag,'status':'INCONCLUSIVE','reason':'No parseable Claude JSON result; check authentication/permissions/CLI version', 'exitCode':result.returncode})
            continue
        usage = data.get('modelUsage')
        usage = usage if isinstance(usage, dict) else {}
        models=list(usage.keys())
        # modelUsage is authoritative usage evidence but doesn't guarantee *which agent* used a model.
        matched=[m for m in models if family(m)==expected]
        tool_uses = delegation_tool_uses(records)
        entry={'test':tag,'expectedFamily':expected,'modelsObserved':models,'reportedCostUSD':finite_or_none(data.get('total_cost_usd')),'exitCode':result.returncode}
        if result.returncode != 0 or not matched:
            entry['status']='INCONCLUSIVE'
        elif not delegation:
            # Main-session case: the prompt forbids delegation, so report it if it happened anyway.
            if tool_uses:
                entry['status']='UNEXPECTED: delegation appeared although the prompt said not to delegate'
                entry['delegationToolUses']=tool_uses
            else:
                entry['status']='OBSERVED'
        else:
            # Claude Code uses Haiku for internal side tasks, so a Haiku entry alone proves nothing.
            total = sum(token_total(v) for v in usage.values())
            share = sum(token_total(usage[m]) for m in matched) / total if total else 0.0
            entry['expectedModelTokenShare'] = round(share, 3)
            if tool_uses:
                entry['status']='PARTIAL: delegation tool use seen and expected model has usage; verify agent-to-model attribution in /tasks or subagent status line'
                entry['delegationToolUses']=tool_uses
            elif tool_uses is None and share >= 0.25:
                entry['status']='PARTIAL: no tool-use records in this output; expected model has material token usage (heuristic). Verify attribution in /tasks or subagent status line'
            else:
                entry['status']='UNVERIFIED: expected model appears in usage but no evidence the subagent was actually used (it may be an internal side task)'
        record.append(entry)
    if out:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'tests':record,'note':'Evidence-only: no prompt/output text stored. /tasks or subagent status verifies attribution.'},indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for item in record:
        print(item['test'],item['status'],'models:',','.join(item.get('modelsObserved',[])))
    print('No claim of complete routing verification without live subagent model attribution.')
    return 0 if all(x['status'].startswith(('OBSERVED','PARTIAL')) for x in record) else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',action='store_true',help='Explicitly initiate model calls')
    ap.add_argument('--approve-usage',action='store_true',help='I approve the usage costs of these tests')
    ap.add_argument('--claude-path',default='claude')
    ap.add_argument('--timeout',type=int,default=180)
    ap.add_argument('--output',type=Path,help='Sanitized JSON evidence output')
    args=ap.parse_args()
    if not(args.run and args.approve_usage):
        print('DRY RUN: 3 Claude invocations: observe default main model, request Explore/Haiku, request deep-reasoner/Opus.')
        print('These calls consume usage and do NOT auto-approve Fable.')
        print('To execute: python live_smoke.py --run --approve-usage [--output result.json]')
        raise SystemExit(0)
    with tempfile.TemporaryDirectory(prefix='routing-smoke-') as folder:
        Path(folder,'routing_smoke.txt').write_text('Evidence-only routing smoke test.\n',encoding='utf-8')
        try:
            raise SystemExit(run(args.claude_path,folder,args.output,args.timeout))
        except RuntimeError as error:
            print('ERROR:',error,file=sys.stderr)
            raise SystemExit(1)
