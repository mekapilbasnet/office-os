#!/usr/bin/env python3
"""Office OS + Dynamic Routing: reversible, conflict-aware, standard-library manager.

Use `plan` before `install --apply`. Never modify unrelated Claude Code settings.
The Office OS skill is the parent; this tool manages its model-routing installation.
This cannot guarantee actual model selection by Claude Code.
"""
import argparse
import base64
import copy
import datetime
import hashlib
import json
import os
import shlex
import stat
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
OFFICE = SOURCE.parent
MANIFEST = json.loads((SOURCE / 'manifest.json').read_text(encoding='utf-8'))
LEGACY = MANIFEST['legacy_v3_hashes']
# Fixed package manifest: never absorb user-added files in the installed Office OS tree.
OWNED = {
    'skills/office-os/' + rel: '../' + rel
    for rel in MANIFEST['owned_office_files']
}
OWNED.update({
    'rules/model-routing.md': '../references/model-routing.md',
    'agents/Explore.md': 'agents/Explore.md',
    'agents/deep-reasoner.md': 'agents/deep-reasoner.md',
    'agents/reviewer.md': 'agents/reviewer.md',
    'commands/dynamic-routing.md': 'commands/dynamic-routing.md',
})
PROFILES = {'economy': 'Avoid unnecessary delegation; use Opus only for unresolved material risk or substantial uncertainty.',
            'balanced': 'Use Haiku for meaningful discovery and Opus for genuinely difficult investigation; keep routine implementation on Sonnet.',
            'quality': 'Escalate ambiguity and high-impact decisions to Opus earlier while keeping routine implementation on Sonnet.'}
OFF_RULE = ("# Office OS Dynamic Routing: disabled\n\n"
            "ROUTING_STATE: OFF\n\n"
            "Dynamic Routing is disabled by explicit user choice. Do NOT apply this "
            "package's automatic model-routing preferences, model-based delegation, "
            "or automatic escalation. Preserve normal Claude Code behavior, manually "
            "selected models, and existing project instructions. Office OS business "
            "workflows are still available without packaged model routing. "
            "Run `/dynamic-routing on` to re-enable automatic routing after a new session.\n").encode('utf-8')


def active_rule_bytes(enabled, profile='balanced'):
    if not enabled:
        return OFF_RULE
    if profile not in PROFILES:
        raise ValueError('Unsupported routing profile: ' + profile)
    body = (SOURCE / '../references/model-routing.md').read_bytes()
    return body + ('\n\n## Active installed routing profile\n\nPROFILE_STATE: ' + profile.upper() + '\n\n' + PROFILES[profile] + '\n').encode('utf-8')


MISSING = object()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(path):
    return path.read_bytes() if path.is_file() else None


def encode(data):
    return None if data is None else base64.b64encode(data).decode('ascii')


def decode(data):
    return None if data is None else base64.b64decode(data)


def read_json(path, default=None):
    if not path.exists():
        return copy.deepcopy(default)
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'Expected a JSON object: {path}')
    return value


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.routing-temp-' + uuid.uuid4().hex[:8])
    try:
        temp.write_bytes(data)
        # Preserve permissions of existing settings files; protect new files by default.
        old_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
        os.chmod(temp, old_mode)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def remove(path):
    if path.is_file():
        path.unlink()


def json_bytes(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def command_line(script):
    """Status commands work under POSIX and PowerShell/Git Bash on Windows."""
    python = sys.executable.replace('\\', '/')
    script = str(script).replace('\\', '/')
    if os.name == 'nt':
        return subprocess.list2cmdline([python, script])
    return f'{shlex.quote(python)} {shlex.quote(script)}'


def desired_settings(cfg, current, args, enabled=True):
    desired = copy.deepcopy(current)
    warnings = []
    touched = {}
    settings = {
        'statusLine': 'skills/office-os/routing-tools/scripts/statusline.py',
        'subagentStatusLine': 'skills/office-os/routing-tools/scripts/subagent_statusline.py',
    }
    for key, dest in settings.items():
        proposed = {'type': 'command', 'command': command_line(cfg / dest)}
        if key not in current or args.replace_status_lines:
            if current.get(key, MISSING) != proposed:
                touched[key] = {'before_exists': key in current, 'before': current.get(key), 'after': proposed}
                desired[key] = proposed
        elif current[key] != proposed:
            warnings.append(f'Existing {key} preserved. Model visibility from this package is not guaranteed for that line. Use --replace-status-lines to opt in.')
    main_model = MANIFEST['default_main_model']
    if enabled and ('model' not in current or args.set_main_model):
        if current.get('model', MISSING) != main_model:
            touched['model'] = {'before_exists': 'model' in current, 'before': current.get('model'), 'after': main_model}
            desired['model'] = main_model
    elif 'model' in current and current['model'] != main_model:
        warnings.append(f"Existing default model {current['model']!r} preserved. Use --set-main-model to switch to Sonnet.")
    env = current.get('env')
    if isinstance(env, dict) and str(env.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE', '')).lower() in ('1', 'true'):
        warnings.append('settings.json forces subagent model: per-agent Haiku/Opus routing may not take effect; no environment setting was changed.')
    if os.environ.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE', '').lower() in ('1', 'true'):
        warnings.append('Current shell forces subagent model: effective models may differ from agent definitions.')
    if os.environ.get('ANTHROPIC_MODEL'):
        warnings.append('ANTHROPIC_MODEL is set in this shell; it may override the user default model.')
    for key in ('disableAllHooks', 'allowManagedHooksOnly'):
        if current.get(key):
            warnings.append(f'{key} is enabled at user level; status line commands may be suppressed.')
    return desired, touched, warnings


def load_state(cfg):
    return read_json(cfg / 'office-os-routing/state.json', default=None)


def plan(cfg, args):
    state = load_state(cfg)
    changes, conflicts, warnings = [], [], []
    proposed_files = {}
    if (cfg / 'dynamic-routing/state.json').is_file():
        conflicts.append('Standalone Dynamic Routing is already managed here. Preview and uninstall it with its original manager before installing Office OS, to avoid competing global rules.')
    enabled = (state or {}).get('enabled', True)
    for dest, src in OWNED.items():
        expected = active_rule_bytes(enabled, (state or {}).get('profile','balanced')) if dest == 'rules/model-routing.md' else (SOURCE / src).read_bytes()
        existing = raw(cfg / dest)
        current_hash = sha(existing) if existing is not None else None
        last_owned = (state or {}).get('files', {}).get(dest, {}).get('installed_sha')
        safe_previous = current_hash == LEGACY.get(dest) and state is None
        if existing == expected:
            status = 'unchanged'
        elif existing is None:
            status = 'create'
        elif safe_previous or (last_owned and last_owned == current_hash):
            status = 'upgrade'  # prior v3 pristine or standalone install intact
        elif args.replace:
            status = 'explicit-replace'
        else:
            status = 'CONFLICT'
            conflicts.append(f'{dest}: existing unrecognized or edited file; preserve until explicit --replace.')
        changes.append((dest, status))
        proposed_files[dest] = expected

    settings_path = cfg / 'settings.json'
    current = read_json(settings_path, default={})
    updated, touched, warns = desired_settings(cfg, current, args, enabled=(state or {}).get('enabled', True))
    warnings += warns
    for key in touched:
        changes.append((f'settings.json#{key}', 'set/update'))
    if state and state.get('version') != MANIFEST['version']:
        warnings.append(f"Existing managed version {state.get('version')} will upgrade to {MANIFEST['version']}")
    warnings.append('Project/local/managed settings, CLI flags, provider aliases and automatic fallback are not controllable here.')
    return changes, conflicts, warnings, proposed_files, current, updated, touched, state


def summarize(changes, conflicts, warnings):
    for dest, status in changes:
        print(f'{status.upper():17} {dest}')
    for item in conflicts:
        print(f'CONFLICT  {item}')
    for item in warnings:
        print(f'NOTE      {item}')


def snapshot(cfg, paths):
    """Capture exact before bytes, including settings.json and state.json."""
    return {name: encode(raw(cfg / name)) for name in paths}


def restore_snapshot(cfg, captured):
    for name, b64 in captured.items():
        p = cfg / name
        data = decode(b64)
        if data is None:
            remove(p)
        else:
            save(p, data)


def backup_dir(cfg):
    ident = datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8]
    folder = cfg / 'office-os-routing/backups' / ident
    folder.mkdir(parents=True, exist_ok=False)
    os.chmod(folder, 0o700)  # Backups include full settings.json and may contain credentials.
    return folder


def write_backup(cfg, before, after, operation, backup_root):
    # A record is created before modifying files, then gets the final after hashes.
    record = {'operation': operation, 'before': before, 'after_hashes': after}
    save(backup_root / 'backup.json', json_bytes(record))


def do_install(cfg, args):
    changes, conflicts, warnings, proposed, current, updated, touched, prev_state = plan(cfg, args)
    summarize(changes, conflicts, warnings)
    if conflicts:
        raise RuntimeError('Install stopped because existing configuration would be overwritten. Review and rerun with explicit --replace if intended.')
    if not args.apply:
        print('PREVIEW ONLY. Rerun with install --apply to make these changes.')
        return
    cfg.mkdir(parents=True, exist_ok=True)
    file_changes = {k: v for k, v in proposed.items() if raw(cfg / k) != v}
    changed_settings = current != updated
    if not file_changes and not changed_settings and prev_state and prev_state.get('version') == MANIFEST['version']:
        print('ALREADY INSTALLED: configuration matches integrated Office OS; no changes or new backups.')
        return
    meta_path = 'office-os-routing/state.json'
    paths = sorted(set(file_changes) | ({'settings.json'} if changed_settings else set()) | {meta_path})
    before = snapshot(cfg, paths)
    back = backup_dir(cfg)
    # Keep initial originals across version upgrades for an uninstall that restores v3.
    initial_files = copy.deepcopy((prev_state or {}).get('originals', {}))
    current_files = copy.deepcopy((prev_state or {}).get('files', {}))
    for path in OWNED:
        if path not in initial_files:
            initial_files[path] = encode(raw(cfg / path))
        current_files[path] = {'installed_sha': sha(proposed[path])}
    initial_keys = copy.deepcopy((prev_state or {}).get('settings_originals', {}))
    installed_keys = copy.deepcopy((prev_state or {}).get('settings_installed', {}))
    for key, item in touched.items():
        if key not in initial_keys:
            initial_keys[key] = {'existed': item['before_exists'], 'value': item['before']}
        installed_keys[key] = item['after']
    state = {
        'version': MANIFEST['version'], 'enabled': (prev_state or {}).get('enabled', True),
        'profile': (prev_state or {}).get('profile', MANIFEST['default_profile']), 'files': current_files,
        'originals': initial_files, 'settings_originals': initial_keys,
        'settings_installed': installed_keys, 'auto_set_model': (prev_state or {}).get('auto_set_model', 'model' in initial_keys and not initial_keys['model']['existed']), 'last_backup': str(back),
    }
    try:
        write_backup(cfg, before, {}, 'install', back)
        for relative, content in file_changes.items():
            save(cfg / relative, content)
        if changed_settings:
            save(cfg / 'settings.json', json_bytes(updated))
        save(cfg / meta_path, json_bytes(state))
        after = {name: sha(raw(cfg / name)) if raw(cfg / name) is not None else None for name in paths}
        write_backup(cfg, before, after, 'install', back)
    except Exception:
        restore_snapshot(cfg, before)
        raise
    print(f'INSTALLED Office OS v{MANIFEST["version"]}. Backup: {back}')
    print('Static files installed; use verify and live smoke tests to check actual routing. Restart Claude Code if new agents or skills are not visible.')


def do_verify(cfg, args):
    state = load_state(cfg)
    errors, warnings = [], []
    enabled = (state or {}).get('enabled', True)
    for dest, src in OWNED.items():
        expected = active_rule_bytes(enabled, (state or {}).get('profile','balanced')) if dest == 'rules/model-routing.md' else (SOURCE / src).read_bytes()
        data = raw(cfg / dest)
        if data is None:
            errors.append(f'Missing {dest}')
        elif data != expected:
            errors.append(f'Unexpected content in {dest}; possible user customization or different package version')
        else:
            print(f'PASS  {dest}')
    rule = raw(cfg / 'rules/model-routing.md') or b''
    required = [b'NEVER use Fable automatically', b'Routing observability', b'Balanced', b'ROUTING_STATE: ON'] if enabled else [b'ROUTING_STATE: OFF', b'Dynamic Routing is disabled']
    for phrase in required:
        if phrase not in rule:
            errors.append('Missing required routing policy provision: ' + phrase.decode())
    agent_expected = [(filename + '.md', model) for filename, model in MANIFEST['agents'].items()]
    for agent, model in agent_expected:
        data = (raw(cfg / 'agents' / agent) or b'').decode('utf-8', errors='replace')
        if f'model: {model}' not in data:
            errors.append(f'{agent} does not specify {model}')
        if 'tools: Read, Grep, Glob' not in data:
            errors.append(f'{agent} missing read-only tool list')
    skill = (raw(cfg / 'skills/office-os/SKILL.md') or b'').decode('utf-8', errors='replace')
    if not skill.startswith('---\n') or 'name: office-os' not in skill or '## Model routing in Claude Code' not in skill:
        errors.append('Office OS skill missing or model-routing integration absent')
    current = read_json(cfg / 'settings.json', default={})
    if enabled and current.get('model') != MANIFEST['default_main_model']:
        warnings.append(f"Main default is {current.get('model')!r}, not sonnet. Overrides may be deliberate.")
    for key, dest in [('statusLine', 'statusline.py'), ('subagentStatusLine', 'subagent_statusline.py')]:
        val = current.get(key)
        if not isinstance(val, dict) or 'office-os/routing-tools/scripts/' + dest not in val.get('command', ''):
            warnings.append(f'Custom package {key} not active (may be deliberately preserved).')
    env = current.get('env')
    if isinstance(env, dict) and str(env.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE','')).lower() in ('1','true'):
        errors.append('Settings force all subagent models; this overrides individual agent model assignments')
    if os.environ.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE','').lower() in ('1','true'):
        warnings.append('Current process environment forces subagent models.')
    if state and state.get('profile','balanced') not in PROFILES:
        errors.append('Unknown configured routing profile')
    if enabled and state and ('PROFILE_STATE: ' + state.get('profile','balanced').upper()).encode() not in rule:
        errors.append('Global rule does not match selected routing profile')
    fallback = current.get('fallbackModel')
    if isinstance(fallback, list) and any('fable' in str(m).lower() or str(m).lower() == 'best' for m in fallback):
        errors.append('Automatic fallback contains approval-only Fable/best model; remove it before using this package')
    elif fallback is not None and not isinstance(fallback, list):
        errors.append('fallbackModel must be an array')
    elif fallback:
        print('PASS  Configured fallback (effective model still must be observed):', ', '.join(str(x) for x in fallback))
    if not state:
        errors.append('Missing Office OS routing installation state')
    elif state.get('version') != MANIFEST['version']:
        warnings.append('Installed version differs from source package; verification may be mismatched')
    if args.claude_native:
        cli = shutil.which('claude')
        if cli:
            run = subprocess.run([cli, 'plugin', 'validate', str(cfg / 'agents')], text=True, capture_output=True, timeout=45, check=False)
            if run.returncode:
                warnings.append('Claude native validation failed or is unsupported: ' + (run.stderr or run.stdout).strip()[:280])
            else:
                print('PASS  Optional Claude native validation')
        else:
            warnings.append('Claude CLI is not available; native validation skipped.')
    for w in warnings: print('WARN ', w)
    for e in errors: print('FAIL ', e)
    print('ROUTING STATE:', 'ON (automatic)' if enabled else 'OFF (manual Claude model selection)')
    print('STATIC VERIFICATION:', 'PASSED' if not errors else 'FAILED')
    print('LIVE ROUTING: NOT TESTED (requires user-authenticated Claude Code session and model usage)')
    return 1 if errors else 0


def do_diagnose(cfg, args):
    settings = read_json(cfg / 'settings.json', default={})
    print('Config directory:', cfg)
    found_state = load_state(cfg) or {}
    print('Installed Office OS routing state:', found_state.get('version', 'not managed'))
    print('Automatic routing:', 'ON' if found_state.get('enabled', True) else 'OFF')
    print('Routing profile:', found_state.get('profile','balanced'))
    print('User-level model:', settings.get('model', '[account default]'))
    for key in ('statusLine', 'subagentStatusLine'):
        val = settings.get(key)
        print(key + ':', 'office-os' if isinstance(val, dict) and 'office-os/routing-tools/scripts/' in val.get('command','') else ('custom' if val else 'unset'))
    print('CLI:', shutil.which('claude') or 'not found')
    if shutil.which('claude'):
        try:
            v = subprocess.run(['claude', '--version'], text=True, capture_output=True, timeout=6, check=False)
            print('CLI version:', (v.stdout or v.stderr).strip()[:160])
        except (OSError, subprocess.TimeoutExpired):
            print('CLI version: unavailable')
    print('Forced subagent model in current environment:', 'YES' if os.environ.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE', '').lower() in ('1','true') else 'no')
    env = settings.get('env') or {}
    print('Forced subagent model in user settings:', 'YES' if isinstance(env,dict) and str(env.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE','')).lower() in ('1','true') else 'no')
    print('Other settings (managed/project/CLI) and actual models: inspect in a live Claude Code session; never inferred here.')
    return do_verify(cfg, args)


def do_status(cfg):
    state = load_state(cfg)
    if not state:
        print('NOT INSTALLED: no Office OS routing manager state. Nothing is automatically enabled by this package.')
        return 1
    enabled = state.get('enabled', True)
    expected_hash = state.get('files', {}).get('rules/model-routing.md', {}).get('installed_sha')
    live_rule = raw(cfg / 'rules/model-routing.md')
    if live_rule is None or sha(live_rule) != expected_hash:
        print('UNKNOWN: routing policy was changed outside the manager. No state claimed.')
        return 1
    print('DYNAMIC ROUTING: ' + ('ON (auto-activated)' if enabled else 'OFF'))
    print('PROFILE:', state.get('profile','balanced').upper())
    print('Main model and model status lines are not affected by on/off.')
    return 0


def do_toggle(cfg, enabled, apply):
    state = load_state(cfg)
    if not state:
        raise RuntimeError('No integrated Office OS installation found. Install the combined package first.')
    path = 'rules/model-routing.md'
    expected_sha = state.get('files', {}).get(path, {}).get('installed_sha')
    live = raw(cfg / path)
    if live is None or sha(live) != expected_sha:
        raise RuntimeError('Routing rule changed outside manager; refusing to overwrite custom edits.')
    existing = state.get('enabled', True)
    if existing == enabled:
        print('DYNAMIC ROUTING ALREADY ' + ('ON' if enabled else 'OFF') + ': no changes needed.')
        return
    current = read_json(cfg / 'settings.json', default={})
    desired = copy.deepcopy(current)
    # Only undo the Sonnet default if this installer introduced it on an empty
    # model setting. Preserve every existing/custom selection, including Opus.
    auto_main = state.get('auto_set_model',
                          'model' in state.get('settings_installed', {})
                          and not state.get('settings_originals', {}).get('model', {}).get('existed', True))
    if auto_main:
        if not enabled and current.get('model', MISSING) == state.get('settings_installed', {}).get('model', MISSING):
            desired.pop('model', None)
        elif enabled and 'model' not in current:
            desired['model'] = MANIFEST['default_main_model']
    print('ACTION: ' + ('Enable automatic routing' if enabled else 'Disable automatic routing'))
    print('TOUCH: rules/model-routing.md + office-os-routing/state.json' +
          (' + package-owned main model default' if desired != current else ''))
    print('PRESERVE: Office OS workflows, custom settings, status lines, subagents and manually selected models')
    if not apply:
        print('PREVIEW ONLY. Rerun with ' + ('on' if enabled else 'off') + ' --apply.')
        return
    targets = [path, 'office-os-routing/state.json']
    if desired != current:
        targets.append('settings.json')
    before = snapshot(cfg, targets)
    back = backup_dir(cfg)
    try:
        write_backup(cfg, before, {}, 'toggle_' + ('on' if enabled else 'off'), back)
        content = active_rule_bytes(enabled, state.get('profile','balanced'))
        save(cfg / path, content)
        state['enabled'] = enabled
        state['auto_set_model'] = bool(auto_main)
        state['files'][path]['installed_sha'] = sha(content)
        if desired != current:
            if 'model' in desired:
                state['settings_installed']['model'] = desired['model']
            else:
                state['settings_installed'].pop('model', None)
            save(cfg / 'settings.json', json_bytes(desired))
        state['last_backup'] = str(back)
        save(cfg / 'office-os-routing/state.json', json_bytes(state))
        after = {name: sha(raw(cfg / name)) if raw(cfg / name) is not None else None for name in targets}
        write_backup(cfg, before, after, 'toggle_' + ('on' if enabled else 'off'), back)
    except Exception:
        restore_snapshot(cfg, before)
        raise
    print('DYNAMIC ROUTING ' + ('ON' if enabled else 'OFF') + '. Backup: ' + str(back))
    print('The current conversation should honor this explicit preference now. Start a new Claude Code session to refresh preloaded rules.')


def guarded_change(cfg, operation, paths, callback):
    """Atomic, reversible multi-file manager change."""
    before = snapshot(cfg, paths)
    back = backup_dir(cfg)
    try:
        write_backup(cfg, before, {}, operation, back)
        callback(back)
        after = {name: sha(raw(cfg / name)) if raw(cfg / name) is not None else None for name in paths}
        write_backup(cfg, before, after, operation, back)
    except Exception:
        restore_snapshot(cfg, before)
        raise
    return back


def do_profile(cfg, requested, apply):
    state = load_state(cfg)
    if not state:
        raise RuntimeError('Install the integrated Office OS package first.')
    current = state.get('profile', 'balanced')
    if requested is None:
        print('ROUTING PROFILE:', current.upper(), '(routing ' + ('ON' if state.get('enabled', True) else 'OFF') + ')')
        return
    requested = requested.lower()
    if requested not in PROFILES:
        raise ValueError('Profile must be economy, balanced, or quality.')
    if current == requested:
        print('ALREADY SELECTED:', requested.upper())
        return
    rule_path = 'rules/model-routing.md'
    live = raw(cfg / rule_path)
    expected = state.get('files', {}).get(rule_path, {}).get('installed_sha')
    if live is None or sha(live) != expected:
        raise RuntimeError('Rule changed outside manager; refusing to overwrite custom changes.')
    print(f'PROFILE: {current.upper()} -> {requested.upper()}')
    print('IMPACT:', PROFILES[requested])
    if not apply:
        print('PREVIEW ONLY. Rerun profile ' + requested + ' --apply.')
        return
    def update(back):
        state['last_backup'] = str(back)
        content = active_rule_bytes(state.get('enabled', True), requested)
        save(cfg / rule_path, content)
        state['profile'] = requested
        state['files'][rule_path]['installed_sha'] = sha(content)
        save(cfg / 'office-os-routing/state.json', json_bytes(state))
    back = guarded_change(cfg, 'profile_' + requested, [rule_path, 'office-os-routing/state.json'], update)
    print('PROFILE CHANGED:', requested.upper(), '(open a new Claude session to refresh the loaded rule)')
    print('ROLLBACK BACKUP:', back)


def do_fallback(cfg, selection, apply):
    """Safe opt-in fallback for the *whole session*, including subagents.

    Never add a premium model. A default-only choice avoids inadvertently
    raising every Haiku subagent to Sonnet unless the user approves it.
    """
    state = load_state(cfg)
    if not state:
        raise RuntimeError('Install the integrated Office OS package first.')
    current = read_json(cfg / 'settings.json', default={})
    existing = current.get('fallbackModel', MISSING)
    if selection is None or selection == 'status':
        print('FALLBACK:', existing if existing is not MISSING else 'not configured')
        print('Availability fallback applies to subagents too. Actual model may differ; inspect runtime model IDs.')
        return
    if selection not in ('none', 'sonnet', 'sonnet-haiku'):
        raise ValueError('Allowed fallback modes: none, sonnet, sonnet-haiku.')
    requested = {'none': None, 'sonnet': ['sonnet'], 'sonnet-haiku': ['sonnet', 'haiku']}[selection]
    if isinstance(existing, list) and any('fable' in str(m).lower() or str(m).lower() == 'best' for m in existing):
        print('WARNING: Current fallback contains a premium model and may bypass instructional approval.')
    if requested == (None if existing is MISSING else existing):
        print('FALLBACK ALREADY:', selection)
        return
    print('FALLBACK:', existing if existing is not MISSING else '[unset]', '->', requested if requested else '[none]')
    print('SCOPE: Claude Code can apply this chain to all subagents, including Haiku. Never contains Fable.')
    print('NOTE: This changes ONLY settings.json#fallbackModel; CLI flags and managed settings can override it.')
    if not apply:
        print('PREVIEW ONLY. Rerun fallback ' + selection + ' --apply.')
        return
    updated = copy.deepcopy(current)
    if requested is None:
        updated.pop('fallbackModel', None)
    else:
        updated['fallbackModel'] = requested
    if 'fallbackModel' not in state.get('settings_originals', {}):
        state.setdefault('settings_originals', {})['fallbackModel'] = {
            'existed': existing is not MISSING,
            'value': None if existing is MISSING else existing
        }
    if requested is None:
        if state['settings_originals']['fallbackModel']['existed']:
            state.setdefault('settings_installed', {})['fallbackModel'] = None  # None means intentionally absent
        else:
            state.setdefault('settings_installed', {}).pop('fallbackModel', None)
    else:
        state.setdefault('settings_installed', {})['fallbackModel'] = requested
    def update(back):
        state['last_backup'] = str(back)
        save(cfg / 'settings.json', json_bytes(updated))
        save(cfg / 'office-os-routing/state.json', json_bytes(state))
    back = guarded_change(cfg, 'fallback_' + selection, ['settings.json','office-os-routing/state.json'], update)
    print('FALLBACK UPDATED. Backup:', back)


def do_history(cfg, limit=10):
    """Read opt-in sanitized usage data. Does not record prompts or route decisions."""
    file=cfg/'office-os-routing/usage-history.jsonl'
    if not file.is_file():
        print('NO HISTORY: generate a usage report with --record first.')
        return 0
    records=[json.loads(line) for line in file.read_text(encoding='utf-8').splitlines() if line.strip()]
    for record in records[-limit:]:
        print(record.get('recordedAt','unknown'), 'reported USD:',record.get('reportedTotalCostUSD','unknown'),
              'models:', ', '.join(sorted((record.get('models') or {}).keys())))
    print('Historical aggregates are opt-in; they are not an automatic audit of routing decisions.')
    return 0


def do_export(cfg, path):
    """Portable, sanitized configuration export. No credentials/settings copied."""
    if path is None:
        raise ValueError('Supply --output destination.json')
    state=load_state(cfg)
    if not state:
        raise RuntimeError('Install the integrated Office OS package first.')
    settings=read_json(cfg/'settings.json',default={})
    fallback=settings.get('fallbackModel')
    if fallback not in (None, ['sonnet'], ['sonnet','haiku']):
        fallback='custom (not exported; inspect your settings separately)'
    data={'schemaVersion':1, 'packageVersion':state.get('version'),
          'routingEnabled':state.get('enabled',True), 'profile':state.get('profile','balanced'),
          'fallbackModel':fallback, 'note':'Portable nonsecret snapshot; do not treat as a live runtime guarantee.'}
    output=Path(path).expanduser().resolve()
    if output.exists():
        raise RuntimeError('Export destination already exists; refusing to overwrite it.')
    save(output,json_bytes(data))
    print('EXPORTED NONSECRET ROUTING CONFIG:',output)
    return 0


def cli_version():
    import re
    exe = shutil.which('claude')
    if not exe:
        return None, 'Claude CLI not found'
    try:
        proc = subprocess.run([exe, '--version'], text=True, capture_output=True, timeout=10, check=False)
        label = (proc.stdout or proc.stderr).strip()
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', label)
        return (tuple(map(int, match.groups())) if match else None), label or 'CLI version unavailable'
    except (subprocess.TimeoutExpired, OSError):
        return None, 'Claude CLI version check unavailable'


def do_compatibility(cfg, strict=False):
    version, label = cli_version()
    print('CLAUDE CLI:', label)
    print('RECOMMENDED MINIMUM: 2.1.257 (force-variable semantics and routing features)')
    print('REQUIREMENTS: >=2.1.205 subagent status model, >=2.1.233 agent native validation, >=2.1.247 subagent fallback')
    if version is None:
        print('SKIPPED: Cannot verify installed Claude Code CLI; requires target machine.')
        return 2 if strict else 0
    if version < (2, 1, 257):
        print('UNSUPPORTED: Upgrade Claude Code before enabling all routing features.')
        return 1
    print('PASS  CLI version meets recommended baseline. Provider/model access remains unverified.')
    return 0


def revert_backup(cfg, back, apply):
    record = read_json(back / 'backup.json')
    if not record:
        raise RuntimeError('Backup not found')
    current_mismatches = []
    for name, expected in record['after_hashes'].items():
        actual = raw(cfg / name)
        current = sha(actual) if actual is not None else None
        if current != expected:
            current_mismatches.append(name)
    print('Backup:', back)
    print('Operation:', record['operation'])
    for path in record['before']:
        print('RESTORE ', path)
    if current_mismatches:
        raise RuntimeError('Refusing to overwrite user changes since backup: ' + ', '.join(current_mismatches))
    if not apply:
        print('PREVIEW ONLY. Rerun rollback --apply to restore this backup.')
        return
    # Create a safety snapshot if rollback itself crashes.
    safety = snapshot(cfg, record['before'])
    try:
        restore_snapshot(cfg, record['before'])
    except Exception:
        restore_snapshot(cfg, safety)
        raise
    print('ROLLBACK COMPLETE. Restart Claude Code to reload agents and skills.')


def do_uninstall(cfg, args):
    state = load_state(cfg)
    if not state:
        print('No managed Office OS routing installation found.')
        return
    current = read_json(cfg / 'settings.json', default={})
    new = copy.deepcopy(current)
    conflicts = []
    originals = state.get('originals', {})
    for path, props in state.get('files', {}).items():
        data = raw(cfg / path)
        if data is None or sha(data) != props['installed_sha']:
            conflicts.append(path + ': changed since Office OS installed')
    for key, expected in state.get('settings_installed', {}).items():
        # A None sentinel records package-owned removal of a pre-existing fallbackModel.
        if not ((expected is None and key == 'fallbackModel' and key not in current)
                or current.get(key, MISSING) == expected):
            conflicts.append('settings.json#' + key + ': changed since Office OS installed')
        else:
            original = state['settings_originals'][key]
            if original['existed']:
                new[key] = original['value']
            else:
                new.pop(key, None)
    if conflicts:
        raise RuntimeError('Uninstall stopped to protect user edits:\n  ' + '\n  '.join(conflicts))
    print('RESTORE previous contents or remove managed files:')
    for path in state.get('files', {}):
        print(' ', path)
    print('RESTORE installer-owned user setting keys only:', ', '.join(state.get('settings_installed', {})))
    if not args.apply:
        print('PREVIEW ONLY. Rerun uninstall --apply to proceed.')
        return
    paths = list(state.get('files', {})) + ['office-os-routing/state.json']
    if new != current:
        paths.append('settings.json')
    before = snapshot(cfg, paths)
    back = backup_dir(cfg)
    try:
        write_backup(cfg, before, {}, 'uninstall', back)
        for path in state['files']:
            original = decode(originals.get(path))
            if original is None:
                remove(cfg / path)
            else:
                save(cfg / path, original)
        if new != current:
            save(cfg / 'settings.json', json_bytes(new))
        remove(cfg / 'office-os-routing/state.json')
        after = {name: sha(raw(cfg / name)) if raw(cfg / name) is not None else None for name in paths}
        write_backup(cfg, before, after, 'uninstall', back)
    except Exception:
        restore_snapshot(cfg, before)
        raise
    print(f'UNINSTALLED. Rollback backup is retained: {back}')


def main():
    ap = argparse.ArgumentParser(description='Office OS routing manager (preview unless --apply)')
    ap.add_argument('command', nargs='?', choices=['plan', 'install', 'verify', 'diagnose', 'rollback', 'uninstall', 'on', 'off', 'status', 'profile', 'fallback', 'compatibility', 'usage', 'history', 'export'], default='plan')
    ap.add_argument('value', nargs='?', help='Profile: economy/balanced/quality or fallback: none/sonnet/sonnet-haiku')
    ap.add_argument('--output', help='Destination for sanitized routing configuration export')
    ap.add_argument('--input', help='Claude Code JSON or JSONL result path (usage command)')
    ap.add_argument('--budget-usd', type=float, help='Warning threshold for reported session cost, not an enforced spend limit')
    ap.add_argument('--record', action='store_true', help='Explicitly append sanitized usage to a local history file')
    ap.add_argument('--strict', action='store_true', help='Treat missing Claude CLI as a compatibility-check failure')
    ap.add_argument('--config-dir', help='Override CLAUDE_CONFIG_DIR or ~/.claude')
    ap.add_argument('--apply', action='store_true', help='Explicitly authorize the planned file operations')
    ap.add_argument('--replace', action='store_true', help='Explicitly replace conflicting agent/rule/skill files')
    ap.add_argument('--replace-status-lines', action='store_true', help='Explicitly replace existing status-line settings')
    ap.add_argument('--set-main-model', action='store_true', help='Explicitly set existing main model to sonnet')
    ap.add_argument('--claude-native', action='store_true', help='Also attempt Claude CLI native validation')
    ap.add_argument('--backup', help='Backup directory to rollback (default: most recent managed install backup)')
    args = ap.parse_args()
    cfg = Path(args.config_dir or os.environ.get('CLAUDE_CONFIG_DIR') or (Path.home() / '.claude')).expanduser().resolve()
    try:
        if args.command == 'plan':
            summarize(*plan(cfg, args)[:3])
            print('PREVIEW ONLY. Run install --apply after reviewing changes.')
        elif args.command == 'install':
            do_install(cfg, args)
        elif args.command == 'on':
            do_toggle(cfg, True, args.apply)
        elif args.command == 'off':
            do_toggle(cfg, False, args.apply)
        elif args.command == 'status':
            return do_status(cfg)
        elif args.command == 'profile':
            do_profile(cfg, args.value, args.apply)
        elif args.command == 'fallback':
            do_fallback(cfg, args.value, args.apply)
        elif args.command == 'compatibility':
            return do_compatibility(cfg, args.strict)
        elif args.command == 'history':
            return do_history(cfg)
        elif args.command == 'export':
            return do_export(cfg, args.output)
        elif args.command == 'usage':
            from usage_report import report
            if not args.input:
                raise ValueError('Provide --input /path/to/claude-result.json (never your whole transcript).')
            return report(Path(args.input), cfg if args.record else None, args.budget_usd)
        elif args.command == 'verify':
            return do_verify(cfg, args)
        elif args.command == 'diagnose':
            return do_diagnose(cfg, args)
        elif args.command == 'rollback':
            state = load_state(cfg)
            back = Path(args.backup) if args.backup else Path((state or {}).get('last_backup',''))
            if not args.backup and not state:
                raise RuntimeError('No active Office OS routing install found. Supply --backup with a recorded directory if already uninstalled.')
            revert_backup(cfg, back, args.apply)
        elif args.command == 'uninstall':
            do_uninstall(cfg, args)
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
