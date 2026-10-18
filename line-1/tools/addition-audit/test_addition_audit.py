"""Small behavioral checks for Addition Audit."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name('addition_audit.py')
SPEC = importlib.util.spec_from_file_location('test_addition_audit_impl', SOURCE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AdditionAuditTests(unittest.TestCase):
    def test_demo_distinguishes_complete_and_omitted(self):
        demo = audit.demo()
        self.assertEqual(demo['complete_candidate']['status'], 'checked')
        self.assertEqual(demo['omitted_contribution']['status'], 'review')
        self.assertTrue(demo['omission_detected'])

    def test_shared_addition_is_required_once(self):
        row = audit.audit_candidate('x', 'a\n', 'a\nb\n', 'a\nb\n', 'a\nb\n')
        self.assertEqual(row['status'], 'checked')

    def test_duplicate_addition_from_one_branch_keeps_multiplicity(self):
        row = audit.audit_candidate('x', 'a\n', 'a\nb\nb\n', 'a\n', 'a\nb\n')
        self.assertEqual(row['missing'][0]['required_occurrences'], 2)

    def test_replacement_addition_is_checked(self):
        row = audit.audit_candidate('x', 'old\n', 'new\n', 'old\n', 'old\n')
        self.assertEqual(row['status'], 'review')

    def test_conflict_is_blocked(self):
        row = audit.audit_candidate('x', 'a\n', 'b\n', 'c\n', None, 'content-conflict')
        self.assertEqual(row['status'], 'blocked')

    def test_deleted_candidate_is_explicit(self):
        row = audit.audit_candidate('x', 'a\n', 'a\n', '', None, 'deleted')
        self.assertEqual(row['status'], 'deleted')


if __name__ == '__main__':
    unittest.main()
