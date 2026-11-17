"""Offline checks. Run: python3 -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from priority_evidence import report


def issue(n, date, body):
    return {'number': n, 'created_at': date, 'body': body}


class PriorityEvidenceTests(unittest.TestCase):
    A = '2026-11-17T09:28:54Z'
    B = '2026-11-17T09:29:18Z'

    def test_creation_order_and_seconds(self):
        result = report(issue(1, self.A, 'rubric'), issue(2, self.B, 'first'))
        self.assertEqual(result['creation_time_delta_seconds_2_minus_1'], 24)
        self.assertEqual(result['creation_order'], '1_before_2')
        self.assertEqual(result['first_explicit_standard'], 'UNDETERMINED')

    def test_negation_is_not_semantic_proof(self):
        a = 'No defeat condition, rubric, or counterexample exists here.'
        b = 'I did NOT claim the first explicit, falsifiable standard.'
        result = report(issue(1, self.A, a), issue(2, self.B, b))
        self.assertEqual(result['first_explicit_standard'], 'UNDETERMINED')

    def test_identical_observations_can_hide_opposite_histories(self):
        # H1: criterion existed at #1 creation; H2: added to #1 after #2.
        # Those hidden events are NOT in the GitHub API's current-body observation.
        x = issue(1, self.A, 'Current rubric and failure condition')
        y = issue(2, self.B, 'Current rival standard')
        h1_report = report(x, y)
        h2_report = report(x, y)
        self.assertEqual(h1_report, h2_report)
        self.assertEqual(h1_report['original_body_provenance'], 'REST_ONLY_NO_EDIT_HISTORY')

    def test_verified_no_edits_supports_historical_provenance(self):
        edits = {'issue1': {'createdAt': self.A, 'lastEditedAt': None},
                 'issue2': {'createdAt': self.B, 'lastEditedAt': None}}
        result = report(issue(1, self.A, 'Rubric'), issue(2, self.B, 'First'), edits)
        self.assertEqual(result['original_body_provenance'], 'NO_EDITS_REPORTED_BY_GITHUB')
        self.assertEqual(result['first_explicit_standard'], 'HUMAN_SEMANTIC_REVIEW_REQUIRED')

    def test_edited_record_remains_unverified(self):
        edits = {'issue1': {'createdAt': self.A, 'lastEditedAt': '2026-11-17T10:00:00Z'},
                 'issue2': {'createdAt': self.B, 'lastEditedAt': None}}
        result = report(issue(1, self.A, 'Rubric'), issue(2, self.B, 'First'), edits)
        self.assertEqual(result['original_body_provenance'], 'REST_ONLY_NO_EDIT_HISTORY')
        self.assertEqual(result['first_explicit_standard'], 'UNDETERMINED')

    def test_reverse_order(self):
        result = report(issue(1, self.B, ''), issue(2, self.A, ''))
        self.assertEqual(result['creation_order'], '2_before_1')
        self.assertEqual(result['creation_time_delta_seconds_2_minus_1'], -24)

    def test_body_hash_changes_when_text_changes(self):
        first = report(issue(1, self.A, 'X'), issue(2, self.B, 'Y'))
        second = report(issue(1, self.A, 'Z'), issue(2, self.B, 'Y'))
        self.assertNotEqual(first['observations'][0]['current_body_sha256'], second['observations'][0]['current_body_sha256'])

if __name__ == '__main__':
    unittest.main()
