"""Hostile-input checks for the status lines, live smoke, usage report and skills check."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import unittest

try:  # works for `discover -s tests` and `python -m unittest tests.<module>`
    from _helpers import SKILLS_CHECK, SMOKE, STATUSLINE, SUBAGENT_STATUSLINE, USAGE, ConfigDirCase, run, run_bytes
except ImportError:
    from tests._helpers import SKILLS_CHECK, SMOKE, STATUSLINE, SUBAGENT_STATUSLINE, USAGE, ConfigDirCase, run, run_bytes

WRONG_SHAPES = [
    '[]', 'null', '{}', '"text"', '42', 'true', '', 'not json at all',
    '{"model":"x"}', '{"model":[1]}', '{"model":{"display_name":5}}', '{"workspace":"s"}',
    '{"workspace":{"current_dir":7}}', '{"cwd":["a"]}', '{"context_window":"big"}',
    '{"context_window":{"used_percentage":"high"}}', '{"cost":[1]}', '{"cost":{"total_cost_usd":"1"}}',
    '{"cost":{"total_cost_usd":NaN}}', '{"cost":{"total_cost_usd":Infinity}}',
    '{"context_window":{"used_percentage":NaN}}',
]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StatuslineRobustness(ConfigDirCase):
    def test_main_statusline_always_exits_zero_with_output(self):
        for raw in WRONG_SHAPES:
            with self.subTest(payload=raw):
                r = run([STATUSLINE], input=raw, env=self.env)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.strip())
                self.assertNotIn('Traceback', r.stderr)

    def test_main_statusline_survives_invalid_utf8_input(self):
        for raw in (b'\xff\xfe\x00garbage', b'{"model":{"display_name":"\xff\xfe"}}', b'\x80'):
            with self.subTest(payload=raw):
                r = run_bytes([STATUSLINE], raw, env=self.env)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.strip())

    def test_bool_and_non_finite_numbers_are_not_shown(self):
        r = run([STATUSLINE], input='{"cost":{"total_cost_usd":true},"context_window":{"used_percentage":true}}', env=self.env)
        self.assertNotIn('$1.00', r.stdout)
        self.assertNotIn('context:', r.stdout)
        for bad in ('NaN', 'Infinity', '-Infinity'):
            r = run([STATUSLINE], input='{"cost":{"total_cost_usd":%s}}' % bad, env=self.env)
            self.assertNotIn('est. API', r.stdout)
        r = run([STATUSLINE], input='{"cost":{"total_cost_usd":2.5}}', env=self.env)
        self.assertIn('est. API: $2.50', r.stdout)

    def test_huge_integer_is_ignored_not_a_crash(self):
        huge = '1' + '0' * 400
        r = run([STATUSLINE], input='{"model":{"display_name":"Sonnet"},"cost":{"total_cost_usd":%s},"context_window":{"used_percentage":%s}}' % (huge, huge), env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('Sonnet', r.stdout)
        self.assertNotIn('unknown', r.stdout)

    def test_bad_state_file_never_breaks_the_line(self):
        state = self.cfg / 'office-os-routing/state.json'
        state.parent.mkdir(parents=True)
        payload = json.dumps({'model': {'display_name': 'Sonnet'}})
        for content in (b'[]', b'null', b'"x"', b'42', b'{', b'', b'\xff\xfe\x00bad'):
            with self.subTest(state=content):
                state.write_bytes(content)
                r = run([STATUSLINE], input=payload, env=self.env)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn('Model: Sonnet', r.stdout)
                self.assertNotIn('routing:', r.stdout)

    def test_state_flags_are_strictly_typed(self):
        state = self.cfg / 'office-os-routing/state.json'
        state.parent.mkdir(parents=True)
        payload = json.dumps({'model': {'display_name': 'Sonnet'}})
        cases = [
            ({'enabled': 'false'}, 'routing: OFF'),
            ({'enabled': 0}, 'routing: OFF'),
            ({'enabled': True, 'profile': 'quality'}, 'routing: quality'),
            ({'enabled': True, 'profile': 5}, 'routing: balanced'),
            ({'enabled': True, 'profile': ['x']}, 'routing: balanced'),
            ({'profile': 'economy'}, 'routing: economy'),
        ]
        for data, expected in cases:
            with self.subTest(state=data):
                state.write_text(json.dumps(data), encoding='utf-8')
                self.assertIn(expected, run([STATUSLINE], input=payload, env=self.env).stdout)

    def test_subagent_statusline_wrong_shapes_exit_zero(self):
        shapes = ['[]', 'null', '{}', '"x"', '', 'garbage', '{"tasks":[1]}', '{"tasks":{"a":1}}', '{"tasks":"x"}',
                  '{"tasks":[null,[],"s",{"id":[1]},{"name":"no id"}]}']
        for raw in shapes:
            with self.subTest(payload=raw):
                r = run([SUBAGENT_STATUSLINE], input=raw, env=self.env)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), '')
                self.assertNotIn('Traceback', r.stderr)
        r = run_bytes([SUBAGENT_STATUSLINE], b'\xff\xfe\x00', env=self.env)
        self.assertEqual(r.returncode, 0)

    def test_subagent_bad_tasks_do_not_hide_good_rows(self):
        tasks = [1, None, {'id': 'a', 'description': 12345, 'model': 7, 'name': ['x']},
                 {'id': 'b', 'name': 'Explore', 'model': 'claude-haiku-x', 'status': 'running', 'description': 'café ✓ ' + 'x' * 80},
                 {'id': 'c', 'label': {'nested': 1}}]
        r = run([SUBAGENT_STATUSLINE], input=json.dumps({'tasks': tasks}), env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [json.loads(line) for line in r.stdout.splitlines()]
        self.assertEqual([row['id'] for row in rows], ['a', 'b', 'c'])
        self.assertIn('12345', rows[0]['content'])
        self.assertIn('claude-haiku-x', rows[1]['content'])
        self.assertIn('café', rows[1]['content'])

    def test_subagent_bool_values_are_treated_as_missing(self):
        payload = json.dumps({'tasks': [{'id': True, 'model': 'x'}, {'id': 'ok', 'model': False, 'status': 0, 'name': True}]})
        r = run([SUBAGENT_STATUSLINE], input=payload, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [json.loads(line) for line in r.stdout.splitlines()]
        self.assertEqual([row['id'] for row in rows], ['ok'])
        self.assertIn('[model unresolved]', rows[0]['content'])
        self.assertIn('Agent', rows[0]['content'])
        self.assertNotIn('False', rows[0]['content'])
        self.assertNotIn('[0]', rows[0]['content'])

    def test_subagent_non_ascii_output_with_ascii_locale(self):
        env = dict(self.env, PYTHONIOENCODING='ascii', LC_ALL='C')
        payload = json.dumps({'tasks': [{'id': '1', 'description': '✓ done'}, {'id': '2', 'description': 'plain'}]})
        r = run([SUBAGENT_STATUSLINE], input=payload, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 2)


@unittest.skipIf(os.name == 'nt', 'POSIX fake claude executable')
class LiveSmokeRobustness(ConfigDirCase):
    def fake_claude(self, outputs):
        """Create a fake `claude` that prints a canned JSON file chosen by the prompt text."""
        bin_dir = Path(self.tmp.name) / 'bin'
        bin_dir.mkdir()
        for key, payload in outputs.items():
            (bin_dir / (key + '.json')).write_text(json.dumps(payload), encoding='utf-8')
        script = bin_dir / 'claude'
        script.write_text('#!/bin/sh\nd="$(dirname "$0")"\ncase "$2" in\n *Explore*) cat "$d/explore.json";;\n'
                          ' *deep-reasoner*) cat "$d/reason.json";;\n *) cat "$d/main.json";;\nesac\n', encoding='utf-8')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return script

    def smoke(self, script):
        out = Path(self.tmp.name) / 'evidence.json'
        r = run([SMOKE, '--run', '--approve-usage', '--claude-path', script, '--output', out, '--timeout', '30'], env=self.env)
        evidence = json.loads(out.read_text(encoding='utf-8')) if out.exists() else None
        return r, evidence

    @staticmethod
    def usage(model, tokens):
        return {model: {'inputTokens': tokens, 'outputTokens': 1, 'cacheReadInputTokens': 0, 'cacheCreationInputTokens': 0, 'costUSD': 0.01}}

    def result(self, usage):
        return {'type': 'result', 'total_cost_usd': 0.02, 'modelUsage': usage}

    @staticmethod
    def agent_call():
        return {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': 'Agent', 'input': {}}]}}

    def test_json_array_output_is_handled_and_labels_are_honest(self):
        side_task = self.usage('claude-haiku-x', 5)
        side_task.update(self.usage('claude-sonnet-x', 50000))
        script = self.fake_claude({
            'main': [{'type': 'system'}, self.result(self.usage('claude-sonnet-x', 100))],
            # Haiku only did a tiny internal side task and nothing was delegated.
            'explore': [{'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'hi'}]}}, self.result(side_task)],
            'reason': [{'type': 'system'}, self.agent_call(), self.result({**self.usage('claude-opus-x', 900), **self.usage('claude-sonnet-x', 100)})],
        })
        r, evidence = self.smoke(script)
        self.assertNotIn('Traceback', r.stderr)
        status = {item['test']: item['status'] for item in evidence['tests']}
        self.assertEqual(status['main'], 'OBSERVED')
        self.assertTrue(status['explore'].startswith('UNVERIFIED'), status)
        self.assertTrue(status['reason'].startswith('PARTIAL'), status)
        self.assertEqual(r.returncode, 1)  # UNVERIFIED must not read as success

    def test_dict_output_without_tool_records_needs_material_usage(self):
        weak = self.result({**self.usage('claude-haiku-x', 10), **self.usage('claude-sonnet-x', 90000)})
        strong = self.result({**self.usage('claude-opus-x', 9000), **self.usage('claude-sonnet-x', 1000)})
        script = self.fake_claude({'main': self.result(self.usage('claude-sonnet-x', 5)), 'explore': weak, 'reason': strong})
        _, evidence = self.smoke(script)
        status = {item['test']: item['status'] for item in evidence['tests']}
        self.assertTrue(status['explore'].startswith('UNVERIFIED'), status)
        self.assertTrue(status['reason'].startswith('PARTIAL'), status)

    def test_ndjson_stream_output_and_cache_tokens_ignored(self):
        bin_dir = Path(self.tmp.name) / 'bin'
        bin_dir.mkdir()
        cache_heavy = {'claude-sonnet-x': {'inputTokens': 10, 'outputTokens': 10, 'cacheReadInputTokens': 10**7, 'cacheCreationInputTokens': 10**6},
                       'claude-haiku-x': {'inputTokens': 400, 'outputTokens': 100}}
        for key, records in {
            'main': [{'type': 'system'}, self.result(self.usage('claude-sonnet-x', 5))],
            'explore': [{'type': 'system'}, self.agent_call(), self.result(cache_heavy)],
            'reason': [{'type': 'system'}, {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'hi'}]}}, self.result(cache_heavy)],
        }.items():
            (bin_dir / (key + '.ndjson')).write_text('\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8')
        script = bin_dir / 'claude'
        script.write_text('#!/bin/sh\nd="$(dirname "$0")"\necho "$@" >> "$d/args.txt"\ncase "$2" in\n *Explore*) cat "$d/explore.ndjson";;\n'
                          ' *deep-reasoner*) cat "$d/reason.ndjson";;\n *) cat "$d/main.ndjson";;\nesac\n', encoding='utf-8')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        r, evidence = self.smoke(script)
        self.assertNotIn('Traceback', r.stderr)
        args = (bin_dir / 'args.txt').read_text(encoding='utf-8')
        self.assertIn('--output-format stream-json', args)
        self.assertIn('--verbose', args)
        status = {item['test']: item['status'] for item in evidence['tests']}
        self.assertTrue(status['explore'].startswith('PARTIAL'), status)
        # The reason case has no delegation tool_use, and Opus is absent, so it is not OBSERVED/PARTIAL.
        self.assertTrue(status['reason'].startswith('INCONCLUSIVE'), status)

    def test_non_finite_tokens_and_cost_keep_evidence_valid_json(self):
        weird = {'type': 'result', 'total_cost_usd': float('inf'),
                 'modelUsage': {'claude-opus-x': {'inputTokens': float('inf'), 'outputTokens': float('nan')},
                                'claude-sonnet-x': {'inputTokens': 10**400, 'outputTokens': 5}}}
        bin_dir = Path(self.tmp.name) / 'bin'
        bin_dir.mkdir()
        (bin_dir / 'out.json').write_text(json.dumps(weird), encoding='utf-8')  # emits Infinity/NaN literals
        script = bin_dir / 'claude'
        script.write_text('#!/bin/sh\ncat "$(dirname "$0")/out.json"\n', encoding='utf-8')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        r, evidence = self.smoke(script)
        self.assertNotIn('Traceback', r.stderr)
        raw = (Path(self.tmp.name) / 'evidence.json').read_text(encoding='utf-8')
        for literal in ('NaN', 'Infinity'):
            self.assertNotIn(literal, raw)
        json.loads(raw, parse_constant=lambda c: self.fail('non-standard JSON constant ' + c))

    def test_unexpected_delegation_in_main_case_is_reported(self):
        delegated = [self.agent_call(), self.result(self.usage('claude-sonnet-x', 10))]
        script = self.fake_claude({'main': delegated, 'explore': delegated, 'reason': delegated})
        r, evidence = self.smoke(script)
        status = {item['test']: item['status'] for item in evidence['tests']}
        self.assertTrue(status['main'].startswith('UNEXPECTED'), status)
        self.assertEqual(r.returncode, 1)

    def test_empty_and_garbage_output_is_inconclusive_not_a_crash(self):
        bin_dir = Path(self.tmp.name) / 'bin'
        bin_dir.mkdir()
        script = bin_dir / 'claude'
        script.write_text('#!/bin/sh\necho "[1, null, \\"x\\"]"\n', encoding='utf-8')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        r, evidence = self.smoke(script)
        self.assertNotIn('Traceback', r.stderr)
        self.assertTrue(all(item['status'] == 'INCONCLUSIVE' for item in evidence['tests']))

    def test_missing_cli_is_a_clean_error(self):
        r = run([SMOKE, '--run', '--approve-usage', '--claude-path', Path(self.tmp.name) / 'nope'], env=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn('Traceback', r.stderr)
        self.assertIn('not found', r.stderr)


class UsageReportRobustness(ConfigDirCase):
    RESULT = {'type': 'result', 'total_cost_usd': 0.25, 'modelUsage': {'claude-sonnet-x': {'inputTokens': 10, 'outputTokens': 5, 'costUSD': 0.25}}}

    def write(self, name, text, encoding='utf-8'):
        path = Path(self.tmp.name) / name
        path.write_bytes(text.encode(encoding))
        return path

    def test_bom_and_utf16_inputs_are_decoded(self):
        line = json.dumps(self.RESULT)
        for name, text, encoding in (('bom.json', line + '\n', 'utf-8-sig'), ('utf16.json', line + '\n', 'utf-16'),
                                     ('utf16be.json', line, 'utf-16-be')):
            with self.subTest(name=name):
                data = text.encode(encoding)
                if encoding == 'utf-16-be':
                    data = b'\xfe\xff' + data
                path = Path(self.tmp.name) / name
                path.write_bytes(data)
                r = run([USAGE, path], env=self.env)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertIn('RESULT RECORDS: 1', r.stdout)

    def test_garbage_lines_are_skipped_with_a_warning(self):
        path = self.write('mixed.jsonl', 'not json\n' + json.dumps(self.RESULT) + '\n{broken\n')
        r = run([USAGE, path], env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('RESULT RECORDS: 1', r.stdout)
        self.assertIn('skipped line 1', r.stderr)
        self.assertIn('skipped line 3', r.stderr)
        self.assertNotIn('Traceback', r.stderr)

    def test_only_garbage_or_binary_exits_cleanly(self):
        for name, data in (('garbage.jsonl', b'nope\nstill nope\n'), ('binary.json', b'\x00\x81\x82\xff\xff\x00')):
            with self.subTest(name=name):
                path = Path(self.tmp.name) / name
                path.write_bytes(data)
                r = run([USAGE, path], env=self.env)
                self.assertEqual(r.returncode, 1)
                self.assertNotIn('Traceback', r.stderr)

    def test_missing_input_is_a_clean_error(self):
        r = run([USAGE, Path(self.tmp.name) / 'absent.json'], env=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn('Traceback', r.stderr)

    def test_invalid_budget_never_writes_history(self):
        path = self.write('ok.jsonl', json.dumps(self.RESULT) + '\n')
        history = self.cfg / 'office-os-routing/usage-history.jsonl'
        for budget in ('-1', 'nan', 'inf', '-inf'):
            with self.subTest(budget=budget):
                r = run([USAGE, path, '--budget-usd=' + budget, '--record', '--config-dir', self.cfg], env=self.env)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertNotIn('Traceback', r.stderr)
                self.assertFalse(history.exists())

    def test_record_and_config_dir_in_standalone_cli(self):
        path = self.write('ok.jsonl', json.dumps(self.RESULT) + '\n')
        history = self.cfg / 'office-os-routing/usage-history.jsonl'
        r = run([USAGE, path, '--record', '--config-dir', self.cfg, '--budget-usd', '1'], env=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(history.read_text(encoding='utf-8').splitlines()), 1)
        r = run([USAGE, path, '--budget-usd', '0.1'], env=self.env)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(len(history.read_text(encoding='utf-8').splitlines()), 1)  # no --record, nothing appended

    def test_non_finite_costs_in_data_are_not_summed(self):
        bad = dict(self.RESULT, total_cost_usd=float('inf'))
        path = self.write('inf.jsonl', json.dumps(bad) + '\n')
        r = run([USAGE, path], env=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn('REPORTED COST USD: $0.0000', r.stdout)


class SkillsCheckRobustness(ConfigDirCase):
    def setUp(self):
        super().setUp()
        self.mod = load('skills_check_under_test', SKILLS_CHECK)

    def skill(self, folder, text):
        path = self.cfg / 'skills' / folder / 'SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding='utf-8')

    def test_frontmatter_name_only(self):
        name = self.mod.frontmatter_name
        self.assertEqual(name('---\nname: real-skill\ndescription: x\n---\nbody'), 'real-skill')
        self.assertEqual(name('---\r\nname: "quoted"\r\n---\r\n'), 'quoted')
        self.assertEqual(name('﻿---\nname: bom-skill\n---\n'), 'bom-skill')
        self.assertIsNone(name('# Title\nname: in-body\n'))
        self.assertIsNone(name('---\ndescription: x\n---\nname: after-frontmatter\n'))
        self.assertIsNone(name(''))

    def test_installed_ignores_name_lines_in_the_body(self):
        self.skill('dir-name', '---\nname: plugin:declared\n---\nSome text\nname: sneaky-body-name\n')
        self.skill('plain', '# No frontmatter\nname: another-sneaky\n')
        found = self.mod.installed(self.cfg)
        self.assertTrue({'dir-name', 'declared', 'plain'} <= found)
        self.assertNotIn('sneaky-body-name', found)
        self.assertNotIn('another-sneaky', found)

    def test_bundled_subagents_are_not_reported_as_missing_skills(self):
        self.assertIn('reviewer', self.mod.bundled_subagents())
        self.assertIn('reviewer', self.mod.referenced())  # still named in the routing guide
        r = run([SKILLS_CHECK, '--config-dir', self.cfg], env=self.env)
        missing_line = [line for line in r.stdout.splitlines() if line.startswith('Not installed')][0]
        self.assertNotIn('reviewer', missing_line)

    def test_import_survives_missing_manifest_and_error_is_clear(self):
        broken = Path(self.tmp.name) / 'copy'
        broken.mkdir()
        (broken / 'manifest.json').write_text('{not json', encoding='utf-8')
        self.mod.SOURCE = broken
        with self.assertRaises(RuntimeError) as ctx:
            self.mod.load_manifest()
        self.assertIn('manifest.json', str(ctx.exception))
        (broken / 'manifest.json').unlink()
        with self.assertRaises(RuntimeError):
            self.mod.load_manifest()

    def test_cli_reports_manifest_problem_without_traceback(self):
        copy_dir = Path(self.tmp.name) / 'tools'
        (copy_dir.parent / 'references').mkdir(parents=True, exist_ok=True)
        copy_dir.mkdir()
        (copy_dir / 'skills_check.py').write_text(SKILLS_CHECK.read_text(encoding='utf-8'), encoding='utf-8')
        (copy_dir / 'manifest.json').write_text('[', encoding='utf-8')
        r = run([copy_dir / 'skills_check.py', '--check-removed'], env=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn('Traceback', r.stderr)
        self.assertIn('manifest.json', r.stderr)


if __name__ == '__main__':
    unittest.main()
