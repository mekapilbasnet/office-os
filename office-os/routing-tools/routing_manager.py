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
import re
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
DEFAULT_PROFILE = MANIFEST['default_profile']
BACKUP_KEEP = 20  # newest backups retained; older ones are pruned when a new one is created
STATE_PATH = 'office-os-routing/state.json'
RULE_PATH = 'rules/model-routing.md'
PRIVATE_NAMES = ('settings.json', 'state.json', 'backup.json')  # new files with these names are written 0600
BACKUP_NAME = re.compile(r'^\d{8}-\d{6}(?:-\d{6})?-[0-9a-f]{8}$')
STATUS_LINES = {
    'statusLine': 'skills/office-os/routing-tools/scripts/statusline.py',
    'subagentStatusLine': 'skills/office-os/routing-tools/scripts/subagent_statusline.py',
}
MIN_CLAUDE = tuple(int(part) for part in MANIFEST['minimum_recommended_claude_code'].split('.'))
# Fixed package manifest: never absorb user-added files in the installed Office OS tree.
OWNED = {
    'skills/office-os/' + rel: '../' + rel
    for rel in MANIFEST['owned_office_files']
}
OWNED.update({
    RULE_PATH: '../references/model-routing.md',
    'agents/Explore.md': 'subagents/Explore.md',
    'agents/deep-reasoner.md': 'subagents/deep-reasoner.md',
    'agents/reviewer.md': 'subagents/reviewer.md',
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


def rule_template():
    """Reference text without the leading installer-template blockquote (meaningless once installed)."""
    original = (SOURCE / '../references/model-routing.md').read_bytes()
    lines = original.decode('utf-8').splitlines(keepends=True)
    head = next((i for i, line in enumerate(lines) if line.startswith('# ')), None)
    if head is None:
        return original
    start = head + 1
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = start
    while end < len(lines) and lines[end].startswith('>'):
        end += 1
    if end == start:
        return original
    while end < len(lines) and not lines[end].strip():
        end += 1
    return ''.join(lines[:head + 1] + ['\n'] + lines[end:]).encode('utf-8')


def active_rule_bytes(enabled, profile=None):
    if not enabled:
        return OFF_RULE
    profile = profile or DEFAULT_PROFILE
    if profile not in PROFILES:
        raise ValueError('Unsupported routing profile: ' + str(profile))
    body = rule_template()
    return body + ('\n\n## Active installed routing profile\n\nPROFILE_STATE: ' + profile.upper() + '\n\n' + PROFILES[profile] + '\n').encode('utf-8')


MISSING = object()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(path):
    return path.read_bytes() if path.is_file() else None


def file_hash(path):
    data = raw(path)
    return None if data is None else sha(data)


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


def safe_path(cfg, name):
    """Join a recorded relative name to the config dir, rejecting anything that escapes it.

    The check is lexical on purpose: a dotfile-managed settings.json may be a symlink to
    somewhere else, and that must keep working.
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f'Unsafe path in recorded data: {name!r}')
    root = os.path.normcase(os.path.normpath(str(cfg)))
    target = os.path.normpath(os.path.join(str(cfg), name))
    try:
        inside = os.path.commonpath([root, os.path.normcase(target)]) == root and os.path.normcase(target) != root
    except ValueError:  # different drives on Windows
        inside = False
    if not inside:
        raise ValueError(f'Refusing path outside the Claude config directory: {name!r}')
    return Path(target)


def hashes(cfg, names):
    return {name: file_hash(safe_path(cfg, name)) for name in names}


def save(path, data, private=None):
    """Atomic write. New files follow the umask unless private (settings/state/backups: 0600).

    A symlinked target (dotfile-managed settings.json) is written through, not replaced.
    """
    if private is None:
        private = path.name in PRIVATE_NAMES
    if path.is_symlink():
        path = Path(os.path.realpath(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.routing-temp-' + uuid.uuid4().hex[:8])
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600 if private else 0o666)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        # Preserve permissions of existing files.
        if path.exists():
            os.chmod(temp, stat.S_IMODE(path.stat().st_mode))
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
        # Forward slashes avoid backslash escaping; a Python path with spaces is double-quoted,
        # which works from cmd.exe and Git Bash but would need a `&` prefix under PowerShell.
        return subprocess.list2cmdline([python, script])
    return f'{shlex.quote(python)} {shlex.quote(script)}'


def flag_is_on(value):
    return str(value if value is not None else '').lower() in ('1', 'true')


def settings_force_subagent(settings):
    env = settings.get('env')
    return isinstance(env, dict) and flag_is_on(env.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE'))


def environment_forces_subagent():
    return flag_is_on(os.environ.get('CLAUDE_CODE_SUBAGENT_MODEL_FORCE'))


def has_premium_fallback(fallback):
    return isinstance(fallback, list) and any('fable' in str(m).lower() or str(m).lower() == 'best' for m in fallback)


def state_enabled(state):
    return (state or {}).get('enabled', True)


def state_profile(state):
    return (state or {}).get('profile', DEFAULT_PROFILE)


def _norm_command(text):
    text = str(text).replace('\\', '/')
    return text.lower() if os.name == 'nt' else text


def package_command_state(value, script):
    """None when the setting is not ours; otherwise 'current' or 'stale'.

    Ours means exactly `<interpreter> <our script>`: a user wrapper that merely mentions the script
    (pipes, `bash -c '...'`, extra arguments) is custom and never touched. A command is stale only when
    its interpreter no longer exists (Python moved or removed); a different but working interpreter
    (`py -3` vs `python`, brew vs system) is left alone so reinstalls stay no-ops.
    """
    if not isinstance(value, dict) or not isinstance(value.get('command'), str):
        return None
    try:
        tokens = shlex.split(value['command'], posix=(os.name != 'nt'))
    except ValueError:
        return None
    if len(tokens) != 2:
        return None
    interpreter, target = (token[1:-1] if len(token) > 1 and token[0] == token[-1] and token[0] in '"\'' else token
                           for token in tokens)
    if _norm_command(target) != _norm_command(script):
        return None
    if not os.path.basename(interpreter.replace('\\', '/')).lower().startswith('py'):
        return None  # `cat statusline.py` and similar are not our python invocation
    if value.get('type') != 'command' or not (os.path.isfile(interpreter) or shutil.which(interpreter)):
        return 'stale'
    return 'current'


def is_package_command(value, script):
    """True when a status line setting runs this package's script under the config dir."""
    return package_command_state(value, script) is not None


def status_line_kind(cfg, settings, key):
    """'unset', 'custom', 'stale' (ours but its interpreter is gone) or 'office-os'."""
    value = settings.get(key)
    if not value:
        return 'unset'
    found = package_command_state(value, cfg / STATUS_LINES[key])
    if found is None:
        return 'custom'
    return 'office-os' if found == 'current' else 'stale'


def frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}
    found = {}
    for line in lines[1:]:
        if line.strip() == '---':
            break
        key, sep, value = line.partition(':')
        if sep:
            found[key.strip()] = value.strip()
    return found


def desired_settings(cfg, current, args, enabled=True):
    desired = copy.deepcopy(current)
    warnings = []
    touched = {}
    for key, dest in STATUS_LINES.items():
        proposed = {'type': 'command', 'command': command_line(cfg / dest)}
        existing = current.get(key, MISSING)
        if existing is not MISSING and not args.replace_status_lines and is_package_command(existing, cfg / dest):
            # Ours already: refresh only a stale command (e.g. Python removed), keep extra user fields.
            if package_command_state(existing, cfg / dest) == 'stale':
                proposed = {**existing, **proposed}
                touched[key] = {'before_exists': True, 'before': existing, 'after': proposed, 'refresh': True}
                desired[key] = proposed
            continue
        if existing is MISSING or args.replace_status_lines:
            if existing != proposed:
                touched[key] = {'before_exists': key in current, 'before': current.get(key), 'after': proposed}
                desired[key] = proposed
        elif existing != proposed:
            warnings.append(f'Existing {key} preserved. Model visibility from this package is not guaranteed for that line. Use --replace-status-lines to opt in.')
    main_model = MANIFEST['default_main_model']
    if enabled and ('model' not in current or args.set_main_model):
        if current.get('model', MISSING) != main_model:
            touched['model'] = {'before_exists': 'model' in current, 'before': current.get('model'), 'after': main_model}
            desired['model'] = main_model
            if 'model' not in current:
                warnings.append(f'settings.json has no main model; setting model={main_model}.')
    elif 'model' in current and current['model'] != main_model:
        warnings.append(f"Existing default model {current['model']!r} preserved. Use --set-main-model to switch to Sonnet.")
    if settings_force_subagent(current):
        warnings.append('settings.json forces subagent model: per-agent Haiku/Opus routing may not take effect; no environment setting was changed.')
    if environment_forces_subagent():
        warnings.append('Current shell forces subagent model: effective models may differ from agent definitions.')
    if os.environ.get('ANTHROPIC_MODEL'):
        warnings.append('ANTHROPIC_MODEL is set in this shell; it may override the user default model.')
    for key in ('disableAllHooks', 'allowManagedHooksOnly'):
        if current.get(key):
            warnings.append(f'{key} is enabled at user level; status line commands may be suppressed.')
    return desired, touched, warnings


def validate_state(cfg, state):
    """Reject hand-edited or old state files up front instead of failing later with a KeyError."""
    def bad(reason):
        raise ValueError(f'Invalid {STATE_PATH}: {reason}. Fix or delete it (earlier copies are in office-os-routing/backups).')
    for key, kind in (('version', str), ('files', dict), ('originals', dict),
                      ('settings_originals', dict), ('settings_installed', dict)):
        if key not in state:
            bad(f"missing '{key}'")
        if not isinstance(state[key], kind):
            bad(f"'{key}' must be of type {kind.__name__}")
    if not isinstance(state.get('enabled', True), bool):
        bad("'enabled' must be true or false")
    if not isinstance(state.get('profile', DEFAULT_PROFILE), str):
        bad("'profile' must be text")
    if not isinstance(state.get('last_backup', ''), str):
        bad("'last_backup' must be text")
    for path, props in state['files'].items():
        safe_path(cfg, path)
        if not isinstance(props, dict) or not isinstance(props.get('installed_sha'), str):
            bad(f"files.{path} needs an 'installed_sha'")
    for path, data in state['originals'].items():
        safe_path(cfg, path)
        if data is not None and not isinstance(data, str):
            bad(f'originals.{path} must be text or null')
    for key, item in state['settings_originals'].items():
        if not isinstance(item, dict) or not isinstance(item.get('existed'), bool) or (item['existed'] and 'value' not in item):
            bad(f"settings_originals.{key} needs 'existed' (and 'value' when it existed)")
    for key in state['settings_installed']:
        if key not in state['settings_originals']:
            bad(f"settings_installed.{key} has no matching settings_originals entry")
    if 'created_dirs' in state:  # optional: absent in states written by earlier versions
        if not isinstance(state['created_dirs'], list) or not all(isinstance(d, str) for d in state['created_dirs']):
            bad("'created_dirs' must be a list of text")
        for folder in state['created_dirs']:
            safe_path(cfg, folder)


def load_state(cfg):
    state = read_json(cfg / STATE_PATH, default=None)
    if state is not None:
        validate_state(cfg, state)
    return state


def plan(cfg, args):
    state = load_state(cfg)
    changes, conflicts, warnings = [], [], []
    proposed_files = {}
    if (cfg / 'dynamic-routing/state.json').is_file():
        conflicts.append('Standalone Dynamic Routing is already managed here. Preview and uninstall it with its original manager before installing Office OS, to avoid competing global rules.')
    enabled = state_enabled(state)
    for dest, src in OWNED.items():
        expected = active_rule_bytes(enabled, state_profile(state)) if dest == RULE_PATH else (SOURCE / src).read_bytes()
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
    updated, touched, warns = desired_settings(cfg, current, args, enabled=enabled)
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
    return {name: encode(raw(safe_path(cfg, name))) for name in paths}


def restore_snapshot(cfg, captured):
    for name, b64 in captured.items():
        p = safe_path(cfg, name)
        data = decode(b64)
        if data is None:
            remove(p)
        else:
            save(p, data)


def backup_operation(folder):
    try:
        record = read_json(folder / 'backup.json')
    except (OSError, ValueError):
        return None
    return record.get('operation') if record else None


def prune_backups(root, keep_dir):
    """Keep the newest BACKUP_KEEP backups (always including keep_dir).

    The oldest install backup is never pruned: it is the only full copy of the user's original settings.
    """
    older = sorted(p for p in root.iterdir()
                   if p != keep_dir and BACKUP_NAME.match(p.name) and p.is_dir() and not p.is_symlink())
    protected = next((p for p in older if backup_operation(p) == 'install'), None)
    older = [p for p in older if p != protected]
    for stale in older[:max(0, len(older) - (BACKUP_KEEP - 1))]:
        shutil.rmtree(stale, ignore_errors=True)


def backup_dir(cfg):
    ident = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '-' + uuid.uuid4().hex[:8]
    root = cfg / 'office-os-routing/backups'
    folder = root / ident
    folder.mkdir(parents=True, exist_ok=False)
    os.chmod(folder, 0o700)  # Backups include full settings.json and may contain credentials.
    prune_backups(root, folder)
    return folder


def write_backup(cfg, before, after, operation, backup_root, extra=None):
    # A record is created before modifying files, then gets the final after hashes.
    record = {'operation': operation, 'before': before, 'after_hashes': after, **(extra or {})}
    save(backup_root / 'backup.json', json_bytes(record))


def guarded_change(cfg, operation, paths, callback, extra=None):
    """Atomic, reversible multi-file manager change."""
    before = snapshot(cfg, paths)
    back = backup_dir(cfg)
    try:
        write_backup(cfg, before, {}, operation, back, extra)
        callback(back)
        write_backup(cfg, before, hashes(cfg, paths), operation, back, extra)
    except BaseException:  # includes Ctrl-C: never leave half-written state behind
        restore_snapshot(cfg, before)
        raise
    return back


def managed_dirs(names):
    """Relative (posix) names of every directory above the given managed files, below the config root."""
    found = set()
    for name in names:
        parent = Path(name).parent
        while parent.as_posix() != '.':
            found.add(parent.as_posix())
            parent = parent.parent
    return found


def prune_empty_dirs(cfg, names, created=None):
    """Remove directories left empty after uninstall; only parents of managed files, never the config root.

    `created` lists the directories this package created. Without that record (older state files)
    only the package's own skills/office-os tree is pruned, so a pre-existing empty agents/ survives.
    """
    root = Path(os.path.normpath(str(cfg)))
    own_tree = 'skills/office-os'
    allowed = set(created) if created is not None else None
    folders = set()
    for name in names:
        folder = safe_path(cfg, name).parent
        while folder != root and root in folder.parents:
            rel = folder.relative_to(root).as_posix()
            if rel in allowed if allowed is not None else (rel == own_tree or rel.startswith(own_tree + '/')):
                folders.add(folder)
            folder = folder.parent
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        cache = folder / '__pycache__'
        if cache.is_dir() and not cache.is_symlink() and all(c.suffix == '.pyc' for c in cache.iterdir()):
            shutil.rmtree(cache, ignore_errors=True)
        try:
            folder.rmdir()  # fails (and is skipped) unless the directory is empty
        except OSError:
            pass


def earlier_install_records(cfg):
    """Valid install backup records of earlier runs, oldest first (used when state.json is lost).

    An install killed mid-way leaves its backup (written before any file changed) but no state.
    """
    records = []
    root = cfg / 'office-os-routing/backups'
    if not root.is_dir():
        return records
    for folder in sorted(p for p in root.iterdir() if BACKUP_NAME.match(p.name) and p.is_dir()):
        try:
            record = read_json(folder / 'backup.json')
            if not record or record.get('operation') != 'install':
                continue
            validate_backup(cfg, record)
        except (OSError, ValueError):
            continue
        records.append(record)
    return records


def earlier_install_originals(cfg, records=None):
    """Pre-install contents of managed files (and settings.json) recorded by earlier install backups."""
    found = {}
    for record in earlier_install_records(cfg) if records is None else records:
        for name, data in record['before'].items():
            if name in OWNED or name == 'settings.json':
                found.setdefault(name, data)
    return found


def seed_settings_originals(cfg, updated, touched, original_bytes, initial_keys, installed_keys):
    """Recover installer-owned settings keys that an interrupted install already wrote.

    original_bytes is settings.json as it was before the earliest install attempt (None: no file).
    """
    try:
        original = json.loads(decode(original_bytes).decode('utf-8-sig')) if original_bytes is not None else {}
    except ValueError:
        return
    if not isinstance(original, dict):
        return
    for key in list(STATUS_LINES) + ['model']:
        if key in initial_keys or key not in updated:
            continue
        if key in touched and not touched[key].get('refresh'):
            continue  # set by this run: its recorded before value is already the real one
        if key == 'model':
            ours = updated['model'] == MANIFEST['default_main_model'] and original.get('model', MISSING) != updated['model']
        else:
            ours = is_package_command(updated[key], cfg / STATUS_LINES[key]) and original.get(key, MISSING) != updated[key]
        if ours:
            initial_keys[key] = {'existed': key in original, 'value': original.get(key)}
            installed_keys[key] = updated[key]


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
    paths = sorted(set(file_changes) | ({'settings.json'} if changed_settings else set()) | {STATE_PATH})
    # Keep initial originals across version upgrades for an uninstall that restores v3.
    initial_files = copy.deepcopy((prev_state or {}).get('originals', {}))
    current_files = copy.deepcopy((prev_state or {}).get('files', {}))
    # No state but earlier install backups: an install was killed before saving state.
    earlier = earlier_install_records(cfg) if prev_state is None else []
    interrupted = earlier_install_originals(cfg, earlier)
    for path in OWNED:
        if path not in initial_files:
            existing = raw(cfg / path)
            if existing == proposed[path] and prev_state is None:
                # Identical to the package but no state: either an install that was killed before
                # saving state, or a pristine pre-existing copy. Earlier install backups tell which;
                # without that evidence keep the file as the original so uninstall never deletes it.
                if path in interrupted:
                    initial_files[path] = interrupted[path]
            if path not in initial_files:
                initial_files[path] = encode(existing)
        current_files[path] = {'installed_sha': sha(proposed[path])}
    initial_keys = copy.deepcopy((prev_state or {}).get('settings_originals', {}))
    installed_keys = copy.deepcopy((prev_state or {}).get('settings_installed', {}))
    if prev_state is None and 'settings.json' in interrupted:
        seed_settings_originals(cfg, updated, touched, interrupted['settings.json'], initial_keys, installed_keys)
    for key, item in touched.items():
        if key not in initial_keys:
            initial_keys[key] = {'existed': item['before_exists'], 'value': item['before']}
        installed_keys[key] = item['after']
    # Directories this package creates are the only ones uninstall may remove. States from earlier
    # versions carry no record and keep the legacy behaviour.
    created_dirs = None
    if prev_state is None or 'created_dirs' in prev_state:
        created_dirs = set((prev_state or {}).get('created_dirs', []))
        for record in earlier:
            created_dirs.update(record.get('created_dirs', []))
        created_dirs.update(d for d in managed_dirs(list(OWNED) + [STATE_PATH]) if not (cfg / d).exists())
    state = {
        'version': MANIFEST['version'], 'enabled': state_enabled(prev_state),
        'profile': state_profile(prev_state), 'files': current_files,
        'originals': initial_files, 'settings_originals': initial_keys,
        'settings_installed': installed_keys, 'auto_set_model': (prev_state or {}).get('auto_set_model', 'model' in initial_keys and not initial_keys['model']['existed']),
    }
    if created_dirs is not None:
        state['created_dirs'] = sorted(created_dirs)

    def apply(back):
        state['last_backup'] = str(back)
        for relative, content in file_changes.items():
            save(cfg / relative, content)
        if changed_settings:
            save(cfg / 'settings.json', json_bytes(updated))
        save(cfg / STATE_PATH, json_bytes(state))
    back = guarded_change(cfg, 'install', paths, apply,
                          {'created_dirs': sorted(created_dirs)} if created_dirs is not None else None)
    print(f'INSTALLED Office OS v{MANIFEST["version"]}. Backup: {back}')
    print('Static files installed; use verify and live smoke tests to check actual routing. Restart Claude Code if new agents or skills are not visible.')


def do_verify(cfg, args):
    state = load_state(cfg)
    errors, warnings = [], []
    enabled = state_enabled(state)
    for dest, src in OWNED.items():
        expected = active_rule_bytes(enabled, state_profile(state)) if dest == RULE_PATH else (SOURCE / src).read_bytes()
        data = raw(cfg / dest)
        if data is None:
            errors.append(f'Missing {dest}')
        elif data != expected:
            errors.append(f'Unexpected content in {dest}; possible user customization or different package version')
        else:
            print(f'PASS  {dest}')
    rule = raw(cfg / RULE_PATH) or b''
    required = [b'NEVER use Fable automatically', b'Routing observability', b'Balanced', b'ROUTING_STATE: ON'] if enabled else [b'ROUTING_STATE: OFF', b'Dynamic Routing is disabled']
    for phrase in required:
        if phrase not in rule:
            errors.append('Missing required routing policy provision: ' + phrase.decode())
    for filename, model in MANIFEST['agents'].items():
        data = raw(cfg / 'agents' / (filename + '.md'))
        if data is None:
            continue  # already reported as Missing above
        fields = frontmatter(data.decode('utf-8', errors='replace'))
        if fields.get('model') != model:
            errors.append(f'{filename}.md does not specify model {model}')
        if fields.get('tools') != 'Read, Grep, Glob':
            errors.append(f'{filename}.md missing read-only tool list')
    skill = (raw(cfg / 'skills/office-os/SKILL.md') or b'').decode('utf-8', errors='replace')
    if not skill.startswith('---\n') or 'name: office-os' not in skill or '## Model routing in Claude Code' not in skill:
        errors.append('Office OS skill missing or model-routing integration absent')
    current = read_json(cfg / 'settings.json', default={})
    if enabled and current.get('model') != MANIFEST['default_main_model']:
        warnings.append(f"Main default is {current.get('model')!r}, not sonnet. Overrides may be deliberate.")
    for key in STATUS_LINES:
        kind = status_line_kind(cfg, current, key)
        if kind == 'stale':
            warnings.append(f'Package {key} command is outdated (for example Python moved); rerun install --apply to refresh it.')
        elif kind != 'office-os':
            warnings.append(f'Custom package {key} not active (may be deliberately preserved).')
    if settings_force_subagent(current):
        errors.append('Settings force all subagent models; this overrides individual agent model assignments')
    if environment_forces_subagent():
        warnings.append('Current process environment forces subagent models.')
    if state and state_profile(state) not in PROFILES:
        errors.append('Unknown configured routing profile')
    if enabled and state and ('PROFILE_STATE: ' + str(state_profile(state)).upper()).encode() not in rule:
        errors.append('Global rule does not match selected routing profile')
    fallback = current.get('fallbackModel')
    if has_premium_fallback(fallback):
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
    print('Automatic routing:', 'ON' if state_enabled(found_state) else 'OFF')
    print('Routing profile:', state_profile(found_state))
    print('User-level model:', settings.get('model', '[account default]'))
    for key in STATUS_LINES:
        kind = status_line_kind(cfg, settings, key)
        print(key + ':', 'office-os (outdated command; rerun install --apply)' if kind == 'stale' else kind)
    exe = shutil.which('claude')
    print('CLI:', exe or 'not found')
    if exe:
        print('CLI version:', cli_version(exe)[1][:160])
    print('Forced subagent model in current environment:', 'YES' if environment_forces_subagent() else 'no')
    print('Forced subagent model in user settings:', 'YES' if settings_force_subagent(settings) else 'no')
    print('Other settings (managed/project/CLI) and actual models: inspect in a live Claude Code session; never inferred here.')
    return do_verify(cfg, args)


def do_status(cfg):
    state = load_state(cfg)
    if not state:
        print('NOT INSTALLED: no Office OS routing manager state. Nothing is automatically enabled by this package.')
        return 1
    enabled = state_enabled(state)
    expected_hash = state['files'].get(RULE_PATH, {}).get('installed_sha')
    live_rule = raw(cfg / RULE_PATH)
    if live_rule is None or sha(live_rule) != expected_hash:
        print('UNKNOWN: routing policy was changed outside the manager. No state claimed.')
        return 1
    print('DYNAMIC ROUTING: ' + ('ON (auto-activated)' if enabled else 'OFF'))
    print('PROFILE:', str(state_profile(state)).upper())
    print('Main model and model status lines are not affected by on/off.')
    return 0


def do_toggle(cfg, enabled, apply):
    state = load_state(cfg)
    if not state:
        raise RuntimeError('No integrated Office OS installation found. Install the combined package first.')
    path = RULE_PATH
    expected_sha = state['files'].get(path, {}).get('installed_sha')
    live = raw(cfg / path)
    if live is None or sha(live) != expected_sha:
        raise RuntimeError('Routing rule changed outside manager; refusing to overwrite custom edits.')
    existing = state_enabled(state)
    if existing == enabled:
        print('DYNAMIC ROUTING ALREADY ' + ('ON' if enabled else 'OFF') + ': no changes needed.')
        return
    current = read_json(cfg / 'settings.json', default={})
    desired = copy.deepcopy(current)
    # Only undo the Sonnet default if this installer introduced it on an empty
    # model setting. Preserve every existing/custom selection, including Opus.
    auto_main = state.get('auto_set_model',
                          'model' in state['settings_installed']
                          and not state['settings_originals'].get('model', {}).get('existed', True))
    if auto_main:
        if not enabled and current.get('model', MISSING) == state['settings_installed'].get('model', MISSING):
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
    targets = [path, STATE_PATH]
    if desired != current:
        targets.append('settings.json')

    def update(back):
        content = active_rule_bytes(enabled, state_profile(state))
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
        save(cfg / STATE_PATH, json_bytes(state))
    back = guarded_change(cfg, 'toggle_' + ('on' if enabled else 'off'), targets, update)
    print('DYNAMIC ROUTING ' + ('ON' if enabled else 'OFF') + '. Backup: ' + str(back))
    print('The current conversation should honor this explicit preference now. Start a new Claude Code session to refresh preloaded rules.')


def do_profile(cfg, requested, apply):
    state = load_state(cfg)
    if not state:
        raise RuntimeError('Install the integrated Office OS package first.')
    current = state_profile(state)
    if requested is None:
        print('ROUTING PROFILE:', str(current).upper(), '(routing ' + ('ON' if state_enabled(state) else 'OFF') + ')')
        return
    requested = requested.lower()
    if requested not in PROFILES:
        raise ValueError('Profile must be economy, balanced, or quality.')
    if current == requested:
        print('ALREADY SELECTED:', requested.upper())
        return
    rule_path = RULE_PATH
    live = raw(cfg / rule_path)
    expected = state['files'].get(rule_path, {}).get('installed_sha')
    if live is None or sha(live) != expected:
        raise RuntimeError('Rule changed outside manager; refusing to overwrite custom changes.')
    print(f'PROFILE: {str(current).upper()} -> {requested.upper()}')
    print('IMPACT:', PROFILES[requested])
    if not apply:
        print('PREVIEW ONLY. Rerun profile ' + requested + ' --apply.')
        return
    def update(back):
        state['last_backup'] = str(back)
        content = active_rule_bytes(state_enabled(state), requested)
        save(cfg / rule_path, content)
        state['profile'] = requested
        state['files'][rule_path]['installed_sha'] = sha(content)
        save(cfg / STATE_PATH, json_bytes(state))
    back = guarded_change(cfg, 'profile_' + requested, [rule_path, STATE_PATH], update)
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
    if has_premium_fallback(existing):
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
    if 'fallbackModel' not in state['settings_originals']:
        state['settings_originals']['fallbackModel'] = {
            'existed': existing is not MISSING,
            'value': None if existing is MISSING else existing
        }
    if requested is None:
        if state['settings_originals']['fallbackModel']['existed']:
            state['settings_installed']['fallbackModel'] = None  # None means intentionally absent
        else:
            state['settings_installed'].pop('fallbackModel', None)
    else:
        state['settings_installed']['fallbackModel'] = requested
    def update(back):
        state['last_backup'] = str(back)
        save(cfg / 'settings.json', json_bytes(updated))
        save(cfg / STATE_PATH, json_bytes(state))
    back = guarded_change(cfg, 'fallback_' + selection, ['settings.json', STATE_PATH], update)
    print('FALLBACK UPDATED. Backup:', back)


def do_history(cfg, limit=10):
    """Read opt-in sanitized usage data. Does not record prompts or route decisions."""
    if limit < 1:
        raise ValueError('--limit must be a positive number.')
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
          'routingEnabled':state_enabled(state), 'profile':state_profile(state),
          'fallbackModel':fallback, 'note':'Portable nonsecret snapshot; do not treat as a live runtime guarantee.'}
    output=Path(path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output, 'xb') as handle:  # exclusive create: no check-then-write race, never overwrites
            handle.write(json_bytes(data))
    except FileExistsError:
        raise RuntimeError('Export destination already exists; refusing to overwrite it.')
    print('EXPORTED NONSECRET ROUTING CONFIG:',output)
    return 0


def cli_version(exe=None):
    exe = exe or shutil.which('claude')
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
    minimum = '.'.join(str(part) for part in MIN_CLAUDE)
    print('CLAUDE CLI:', label)
    print(f'RECOMMENDED MINIMUM: {minimum} (force-variable semantics and routing features)')
    print('REQUIREMENTS: >=2.1.205 subagent status model, >=2.1.233 agent native validation, >=2.1.247 subagent fallback')
    if version is None:
        print('SKIPPED: Cannot verify installed Claude Code CLI; requires target machine.')
        return 2 if strict else 0
    if version < MIN_CLAUDE:
        print('UNSUPPORTED: Upgrade Claude Code before enabling all routing features.')
        return 1
    print('PASS  CLI version meets recommended baseline. Provider/model access remains unverified.')
    return 0


def validate_backup(cfg, record):
    """Check a backup record's shape and that every path stays inside the config dir."""
    if not isinstance(record.get('operation'), str):
        raise ValueError('Invalid backup record: missing operation')
    for field in ('before', 'after_hashes'):
        if not isinstance(record.get(field), dict):
            raise ValueError(f'Invalid backup record: missing {field}')
        for name in record[field]:
            safe_path(cfg, name)
    for data in record['before'].values():
        if data is not None:
            if not isinstance(data, str):
                raise ValueError('Invalid backup record: file contents must be text or null')
            decode(data)  # ValueError (binascii.Error) on corrupt base64


def revert_backup(cfg, back, apply):
    record = read_json(back / 'backup.json')
    if not record:
        raise RuntimeError('Backup not found')
    validate_backup(cfg, record)
    current_mismatches = []
    for name, expected in record['after_hashes'].items():
        if file_hash(safe_path(cfg, name)) != expected:
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
    except BaseException:
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
    originals = state['originals']
    for path, props in state['files'].items():
        if file_hash(cfg / path) != props['installed_sha']:
            conflicts.append(path + ': changed since Office OS installed')
    for key, expected in state['settings_installed'].items():
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
    for path in state['files']:
        print(' ', path)
    print('RESTORE installer-owned user setting keys only:', ', '.join(state['settings_installed']))
    if not args.apply:
        print('PREVIEW ONLY. Rerun uninstall --apply to proceed.')
        return
    paths = list(state['files']) + [STATE_PATH]
    if new != current:
        paths.append('settings.json')

    def apply(back):
        for path in state['files']:
            original = decode(originals.get(path))
            if original is None:
                remove(cfg / path)
            else:
                save(cfg / path, original)
        if new != current:
            save(cfg / 'settings.json', json_bytes(new))
        remove(cfg / STATE_PATH)
    back = guarded_change(cfg, 'uninstall', paths, apply)
    prune_empty_dirs(cfg, paths, state.get('created_dirs'))
    print(f'UNINSTALLED. Rollback backup is retained: {back}')


def main():
    ap = argparse.ArgumentParser(description='Office OS routing manager (preview unless --apply)')
    ap.add_argument('command', nargs='?', choices=['plan', 'install', 'verify', 'diagnose', 'rollback', 'uninstall', 'on', 'off', 'status', 'profile', 'fallback', 'compatibility', 'usage', 'history', 'export'], default='plan')
    ap.add_argument('value', nargs='?', help='Profile: economy/balanced/quality or fallback: none/sonnet/sonnet-haiku')
    ap.add_argument('--output', help='Destination for sanitized routing configuration export')
    ap.add_argument('--input', help='Claude Code JSON or JSONL result path (usage command)')
    ap.add_argument('--budget-usd', type=float, help='Warning threshold for reported session cost, not an enforced spend limit')
    ap.add_argument('--record', action='store_true', help='Explicitly append sanitized usage to a local history file')
    ap.add_argument('--limit', type=int, default=10, help='Number of recent usage-history records to show (history command)')
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
            return do_history(cfg, args.limit)
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
            recorded = args.backup or (state or {}).get('last_backup', '')
            if not args.backup and not state:
                raise RuntimeError('No active Office OS routing install found. Supply --backup with a recorded directory if already uninstalled.')
            if not recorded:
                raise RuntimeError('No backup recorded. Supply --backup with a backup directory.')
            revert_backup(cfg, Path(recorded), args.apply)
        elif args.command == 'uninstall':
            do_uninstall(cfg, args)
    except subprocess.TimeoutExpired as error:
        print(f'ERROR: a Claude CLI call timed out after {error.timeout:g} seconds; try again or skip --claude-native.', file=sys.stderr)
        return 1
    except (RuntimeError, ValueError, FileNotFoundError, OSError) as error:
        print('ERROR:', error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('ERROR: interrupted; rollback was attempted. Run verify to check the result.', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
