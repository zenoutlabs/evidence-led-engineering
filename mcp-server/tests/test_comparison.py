import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comparison import EVIDENCE_FIELDS, compare_timings


class ComparisonTests(unittest.TestCase):
    def evidence(self):
        return dict.fromkeys(EVIDENCE_FIELDS, True)

    def test_known_medians_and_percentages(self):
        result = compare_timings([12, 10, 11], [6, 5, 4], self.evidence())
        self.assertEqual(result["baseline"]["median_ms"], 11)
        self.assertEqual(result["candidate"]["median_ms"], 5)
        self.assertEqual(result["observed_median_speedup"], 2.2)
        self.assertAlmostEqual(result["observed_elapsed_reduction_percent"], 600 / 11)
        self.assertTrue(result["declared_evidence_complete"])
        self.assertFalse(result["independent_verification_performed"])
        self.assertEqual(result["scope"], "function")

    def test_regression_equality_and_overlapping_ranges(self):
        slower = compare_timings([1, 2, 3], [2, 3, 4], self.evidence())
        self.assertEqual(slower["candidate_elapsed_direction"], "higher")
        self.assertTrue(slower["ranges_overlap"])
        equal = compare_timings([1, 2, 3], [3, 2, 1], self.evidence())
        self.assertEqual(equal["candidate_elapsed_direction"], "equal")
        self.assertEqual(equal["observed_elapsed_reduction_percent"], 0)

    def test_each_missing_fact_is_reported_and_function_scope_is_limited(self):
        for field in EVIDENCE_FIELDS:
            evidence = self.evidence()
            evidence[field] = False
            result = compare_timings([10, 11, 12], [1, 2, 3], evidence, "function")
            self.assertEqual(result["missing_declared_evidence"], [field])
            self.assertFalse(result["declared_evidence_complete"])
            self.assertTrue(any("whole-workflow" in c for c in result["cautions"]))

    def test_invalid_and_excessive_samples_are_rejected(self):
        invalid = [[], [1, 2], [1] * 101, [0, 1, 2], [-1, 1, 2],
                   [True, 1, 2], ["1", 1, 2], [math.inf, 1, 2],
                   [math.nan, 1, 2], [100_000_000, 1, 2], [1e-12, 1, 2],
                   [10**1000, 1, 2]]
        for samples in invalid:
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                compare_timings(samples, [1, 2, 3], self.evidence())
        with self.assertRaises(ValueError):
            compare_timings([1, 2, 3], [1, 2, 3, 4], self.evidence())

    def test_fact_types_names_and_scope_are_strict(self):
        for facts in ({}, {**self.evidence(), "unknown": True},
                      {**self.evidence(), "same_workload": 1}):
            with self.assertRaises(ValueError):
                compare_timings([1, 2, 3], [1, 2, 3], facts)
        with self.assertRaises(ValueError):
            compare_timings([1, 2, 3], [1, 2, 3], self.evidence(), "production")

    def test_inputs_are_preserved_and_extreme_ratios_stay_finite(self):
        baseline, candidate, evidence = [0.000001] * 100, [86_400_000] * 100, self.evidence()
        result = compare_timings(baseline, candidate, evidence)
        self.assertTrue(math.isfinite(result["observed_median_speedup"]))
        self.assertTrue(math.isfinite(result["observed_elapsed_reduction_percent"]))
        self.assertEqual(baseline, [0.000001] * 100)
        self.assertEqual(candidate, [86_400_000] * 100)
        self.assertEqual(evidence, self.evidence())


if __name__ == "__main__":
    unittest.main()
