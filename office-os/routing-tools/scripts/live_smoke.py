#!/usr/bin/env python3
"""Opt-in authenticated Claude Code smoke test. Records only model IDs/usage, not prompts."""
import argparse
import json
import os
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

def run(cli, cwd, out=None, timeout=180):
    if shutil.which(cli) is None and not Path(cli).is_file():
        raise RuntimeError('Claude CLI not found. Install it and sign in first.')
    record=[]
    for tag, prompt, expected, delegation in TASKS:
        cmd=[cli,'-p',prompt,'--output-format','json','--max-turns','5', '--allowedTools','Read,Glob,Grep,Agent']
        # Do not pin the model: this probes the actual default and loaded routing.
        # Existing user/managed overrides may therefore produce an honest mismatch.
        try:
            result=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=timeout,check=False)
        except subprocess.TimeoutExpired:
            record.append({'test':tag,'status':'INCONCLUSIVE','reason':'timed out'})
            continue
        try:
            data=json.loads(result.stdout)
        except json.JSONDecodeError:
            record.append({'test':tag,'status':'INCONCLUSIVE','reason':'No parseable Claude JSON result; check authentication/permissions/CLI version', 'exitCode':result.returncode})
            continue
        models=list((data.get('modelUsage') or {}).keys())
        # modelUsage is authoritative usage evidence but doesn't guarantee *which agent* used a model.
        matched=[m for m in models if family(m)==expected]
        status='OBSERVED' if matched and result.returncode==0 else 'INCONCLUSIVE'
        if delegation and matched:
            status='PARTIAL: model usage observed; verify agent-to-model attribution in /tasks or subagent status line'
        record.append({'test':tag,'status':status,'expectedFamily':expected,'modelsObserved':models,'reportedCostUSD':data.get('total_cost_usd'), 'exitCode':result.returncode})
    if out:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'tests':record,'note':'Evidence-only: no prompt/output text stored. /tasks or subagent status verifies attribution.'},indent=2)+'\n')
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
        Path(folder,'routing_smoke.txt').write_text('Evidence-only routing smoke test.\n')
        raise SystemExit(run(args.claude_path,folder,args.output,args.timeout))
