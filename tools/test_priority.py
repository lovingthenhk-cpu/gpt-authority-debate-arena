#!/usr/bin/env python3
"""Offline negative controls for check_priority.py. Run: python3 -m unittest -v test_priority.py"""
import unittest
from check_priority import metadata_observations, evidence_lines


class PriorityAuditTests(unittest.TestCase):
    def setUp(self):
        self.issue1 = {
            "created_at": "2026-11-17T09:28:54Z",
            "body": "No defeat condition, rubric, or counterexample exists here.",
        }
        self.issue2 = {
            "created_at": "2026-11-17T09:29:18Z",
            "body": "I did NOT claim the first explicit, falsifiable standard.",
        }
        self.unedited = {
            "first": {"createdAt": "2026-11-17T09:28:54Z", "lastEditedAt": None},
            "second": {"createdAt": "2026-11-17T09:29:18Z", "lastEditedAt": None},
        }

    def test_time_difference_is_24_seconds(self):
        d = metadata_observations(self.issue1, self.issue2, self.unedited)
        self.assertEqual(d["gap_seconds"], 24)
        self.assertTrue(d["issue1_earlier"])
        self.assertEqual(d["edit_status"], "NO_EDITS_RECORDED")

    def test_negated_bodies_do_not_get_semantic_verdict(self):
        d = metadata_observations(self.issue1, self.issue2, self.unedited)
        self.assertEqual(d["semantic_verdict"], "HUMAN_REVIEW_REQUIRED")
        # The dangerous substring check DOES match negations; the metadata
        # validator must never draw a semantic conclusion from this list.
        self.assertTrue(evidence_lines(self.issue1["body"], ["rubric"]))
        self.assertTrue(evidence_lines(self.issue2["body"], ["first explicit"]))

    def test_missing_edit_history_keeps_provenance_unknown(self):
        d = metadata_observations(self.issue1, self.issue2)
        self.assertEqual(d["edit_status"], "NOT_CHECKED")
        self.assertEqual(d["semantic_verdict"], "HUMAN_REVIEW_REQUIRED")

    def test_post_creation_edit_changes_provenance_status(self):
        edited = {"first": {"createdAt": "2026-11-17T09:28:54Z", "lastEditedAt": "2026-11-17T09:40:00Z"},
                  "second": {"createdAt": "2026-11-17T09:29:18Z", "lastEditedAt": None}}
        d = metadata_observations(self.issue1, self.issue2, edited)
        self.assertEqual(d["edit_status"], "AT_LEAST_ONE_BODY_EDIT_RECORDED")
        self.assertEqual(d["semantic_verdict"], "HUMAN_REVIEW_REQUIRED")

    def test_reversed_creation_order(self):
        d = metadata_observations(self.issue2, self.issue1)
        self.assertFalse(d["issue1_earlier"])
        self.assertEqual(d["gap_seconds"], -24)


    def test_fractional_seconds_forward(self):
        first = {"created_at": "2026-11-17T09:28:54.100Z", "body": "x"}
        second = {"created_at": "2026-11-17T09:28:54.900Z", "body": "y"}
        result = metadata_observations(first, second)
        self.assertAlmostEqual(result["gap_seconds"], 0.8)
        self.assertTrue(result["issue1_earlier"])

    def test_fractional_seconds_reverse(self):
        first = {"created_at": "2026-11-17T09:28:54.900Z", "body": "x"}
        second = {"created_at": "2026-11-17T09:28:54.100Z", "body": "y"}
        result = metadata_observations(first, second)
        self.assertAlmostEqual(result["gap_seconds"], -0.8)
        self.assertFalse(result["issue1_earlier"])

    def test_exact_tie(self):
        same = {"created_at": "2026-11-17T09:28:54.100Z", "body": "x"}
        result = metadata_observations(same, same)
        self.assertEqual(result["gap_seconds"], 0)
        self.assertFalse(result["issue1_earlier"])


    def test_wrong_issues_cannot_supply_no_edit_provenance(self):
        wrong = {
            "first": {"createdAt": "2026-11-16T00:00:00Z", "lastEditedAt": None},
            "second": {"createdAt": "2026-11-17T09:29:18Z", "lastEditedAt": None},
        }
        result = metadata_observations(self.issue1, self.issue2, wrong)
        self.assertEqual(result["edit_status"], "MISMATCHED_CREATION_TIMES")

    def test_equivalent_timezone_spelling_is_accepted(self):
        equivalent = {
            "first": {"createdAt": "2026-11-17T18:28:54+09:00", "lastEditedAt": None},
            "second": {"createdAt": "2026-11-17T18:29:18+09:00", "lastEditedAt": None},
        }
        result = metadata_observations(self.issue1, self.issue2, equivalent)
        self.assertEqual(result["edit_status"], "NO_EDITS_RECORDED")

    def test_missing_creation_metadata_is_not_trusted(self):
        incomplete = {
            "first": {"lastEditedAt": None},
            "second": {"lastEditedAt": None},
        }
        result = metadata_observations(self.issue1, self.issue2, incomplete)
        self.assertEqual(result["edit_status"], "INCOMPLETE_EDIT_METADATA")



if __name__ == "__main__":
    unittest.main()
