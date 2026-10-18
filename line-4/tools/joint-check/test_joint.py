import copy
import contextlib
import io
import importlib.util
import itertools
from pathlib import Path
import random
from unittest.mock import patch
import unittest

spec = importlib.util.spec_from_file_location('joint', Path(__file__).with_name('joint.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def catalog(packages, roots=None):
    return {'packages': packages, 'roots': roots or {'app': '*'}}


class JointTests(unittest.TestCase):
    def test_individual_is_not_joint(self):
        data = catalog({'app': {'1': {'dep': '==1'}, '2': {'dep': '==2'}},
                        'dep': {'1': {}, '2': {}}})
        for pins in ({'app': '1'}, {'dep': '2'}):
            self.assertEqual(m.joint_check(data, pins)['status'], 'compatible')
        out = m.joint_check(data, {'app': '1', 'dep': '2'})
        self.assertEqual(out['status'], 'incompatible')
        self.assertEqual(out['checked_assignments'], out['candidate_assignments'])
        self.assertEqual(out['compatible_selections_seen'], 2)

    def test_unreachable_pin_does_not_become_root(self):
        data = catalog({'app': {'1': {}}, 'unused': {'1': {}}})
        self.assertEqual(m.joint_check(data, {'unused': '1'})['status'], 'incompatible')

    def test_branch_presence_and_cycles(self):
        data = catalog({'app': {'1': {}, '2': {'dep': '*'}},
                        'dep': {'1': {'app': '==2'}}})
        out = m.joint_check(data, {'dep': '1'})
        self.assertEqual(out['witness'], {'app': '2', 'dep': '1'})
        self.assertEqual(m.joint_check(data, {'app': '1', 'dep': '1'})['status'], 'incompatible')

    def test_budget_and_exact_boundary(self):
        data = catalog({'app': {'1': {}, '2': {}}})
        out = m.joint_check(data, {'app': '2'}, 1)
        self.assertEqual(out['status'], 'inconclusive')
        self.assertNotIn('witness', out)
        self.assertEqual(m.joint_check(data, {'app': '2'}, 2)['status'], 'compatible')
        self.assertEqual(m.joint_check(data, {'app': '3'}, 2)['status'], 'incompatible')
        self.assertEqual(m.joint_check(data, {'app': '1'}, 1)['status'], 'compatible')

    def test_zero_domain_and_missing_dependency(self):
        data = catalog({'app': {'1': {}}}, {'app': '>2'})
        out = m.joint_check(data, {'app': '1'}, 1)
        self.assertEqual((out['status'], out['checked_assignments']), ('incompatible', 0))
        data = catalog({'app': {'1': {'missing': '*'}}})
        self.assertEqual(m.joint_check(data, {'app': '1'})['status'], 'incompatible')

    def test_normalization_and_no_mutation(self):
        data = catalog({'My_App': {'1.0': {}}}, {'my-app': '*'})
        pins = {'MY.APP': '1'}
        before = copy.deepcopy((data, pins))
        out = m.joint_check(data, pins)
        self.assertEqual(out['witness'], {'my-app': '1.0'})
        self.assertEqual(out['pins'], {'my-app': '1.0'})
        self.assertEqual((data, pins), before)
        other = m.joint_check(data, {'my-app': '9'})
        self.assertEqual(out['catalog_sha256'], other['catalog_sha256'])

    def test_invalid_inputs(self):
        data = catalog({'app': {'1': {}}})
        for pins in ({}, [], {'app': 1}, {'app': 'v1'}, {'A_B': '1', 'a-b': '1'}):
            with self.assertRaises(m.fmt.Invalid):
                m.joint_check(data, pins)
        for budget in (True, 0, -1, 1000001, '1', 1.0):
            with self.assertRaises(m.fmt.Invalid):
                m.joint_check(data, {'app': '1'}, budget)

    def test_historical_metadata(self):
        path = m.CHECKER.parent.parent / 'conflict-core/examples/requests-conflict.json'
        data = m.fmt.load(path)
        data['roots'] = {'requests': '*', 'urllib3': '<2'}
        for pins in ({'requests': '2.25.1'}, {'idna': '3.10'}):
            self.assertEqual(m.joint_check(data, pins)['status'], 'compatible')
        out = m.joint_check(data, {'requests': '2.25.1', 'idna': '3.10'})
        self.assertEqual(out['status'], 'incompatible')
        self.assertEqual(out['checked_assignments'], 216)

    def test_cli_statuses(self):
        for argv, expected in ((['demo'], 0),
                (['demo', '--require', 'requests=2.25.1', '--require', 'idna=3.10'], 1),
                (['demo', '--max-assignments', '1'], 3),
                (['demo', '--require', 'requests==2.25.1'], 2),
                (['demo', '--require', 'my_app=1', '--require', 'MY.APP=2'], 2)):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(argv), expected)

    def test_does_not_call_original_solver_or_predicate(self):
        data = catalog({'app': {'1': {'dep': '*'}}, 'dep': {'1': {}}})
        with patch.object(m.fmt, 'solve', side_effect=AssertionError('solver called')):
            with patch.object(m.fmt, 'accepts', side_effect=AssertionError('predicate called')):
                self.assertEqual(m.joint_check(data, {'dep': '1'})['status'], 'compatible')

    def test_seeded_separate_oracle(self):
        rng = random.Random(3004)
        for _ in range(200):
            names = ['app', 'b', 'c']
            packages = {p: {v: {q: rng.choice(('*', '==1', '==2'))
                                   for q in names if rng.random() < .3}
                            for v in ('1', '2') if rng.random() < .85}
                        for p in names}
            data = catalog(packages)
            solutions = []
            for values in itertools.product(*[[None] + list(packages[p]) for p in names]):
                selected = {p: v for p, v in zip(names, values) if v is not None}
                if 'app' not in selected:
                    continue
                reached, todo, valid = set(), ['app'], True
                while todo and valid:
                    p = todo.pop()
                    if p in reached:
                        continue
                    reached.add(p)
                    for q, constraint in packages[p][selected[p]].items():
                        if q not in selected or not m.fmt.accepts(selected[q], constraint):
                            valid = False
                            break
                        todo.append(q)
                if valid and reached == set(selected):
                    solutions.append(selected)
            for pins in ({'app': '1'}, {'b': '2'}, {'app': '1', 'c': '2'}, {'b': '1', 'c': '2'}):
                expected = any(all(s.get(p) == v for p, v in pins.items()) for s in solutions)
                out = m.joint_check(data, pins)
                self.assertEqual(out['status'], 'compatible' if expected else 'incompatible')
                if expected:
                    self.assertIn(out['witness'], solutions)


if __name__ == '__main__':
    unittest.main()
