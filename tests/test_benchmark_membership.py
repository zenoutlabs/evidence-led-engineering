"""Check benchmark fixtures and bounds. Do not assert a speedup."""

import argparse
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills/evidence-led-performance/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from benchmark_membership import make_fixture, run_benchmark, scan_comparisons, validate_arguments  # noqa: E402
from performance_examples import Item, difference_indexed  # noqa: E402


class BenchmarkTests(unittest.TestCase):
    def args(self, **changes):
        values = dict(n=12, m=7, hit_rate=0.5, seed=1729, repeats=2, reuse_queries=2)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_fixtures_repeat_and_have_requested_hit_count(self):
        first = make_fixture(12, 7, 0.25, 1729, 3)
        self.assertEqual(first, make_fixture(12, 7, 0.25, 1729, 3))
        right, workloads = first
        self.assertEqual([len(difference_indexed(left, right)) for left in workloads], [9, 9, 9])
        self.assertNotEqual(workloads[0], workloads[1])

    def test_operation_counts_include_misses_and_short_circuit_hits(self):
        right = [Item("alpha", 1), Item("alpha", 2), Item("alpha", 3)]
        left = [right[0], right[2], Item("beta", 1)]
        self.assertEqual(scan_comparisons(left, right), 1 + 3 + 3)
        self.assertEqual(scan_comparisons(left, []), 0)

    def test_extreme_hit_rates_and_empty_input(self):
        for n, m, hit_rate, expected in ((10, 5, 0, 10), (10, 5, 1, 0), (0, 0, 0, 0), (10, 0, 0, 10)):
            right, workloads = make_fixture(n, m, hit_rate, 1729, 1)
            self.assertEqual(len(difference_indexed(workloads[0], right)), expected)

    def test_cli_bounds_reject_excess_work_and_invalid_inputs(self):
        changes = [
            {"n": -1}, {"m": 5001}, {"hit_rate": float("nan")},
            {"hit_rate": 1.1}, {"m": 0, "hit_rate": 1}, {"repeats": 0},
            {"reuse_queries": 9}, {"seed": 2**31},
            {"n": 5000, "m": 5000, "repeats": 9, "reuse_queries": 8},
        ]
        for change in changes:
            with self.subTest(change=change), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    validate_arguments(argparse.ArgumentParser(), self.args(**change))
                self.assertEqual(error.exception.code, 2)

    def test_full_run_bound_includes_work_outside_repeated_timings(self):
        args = self.args(n=1100, m=1000, repeats=5, reuse_queries=3)
        timed_only = args.n * args.m * (1 + args.reuse_queries) * args.repeats
        self.assertEqual(timed_only, 22_000_000)
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                validate_arguments(argparse.ArgumentParser(), args)
        self.assertEqual(error.exception.code, 2)

    def test_small_run_checks_equivalent_outputs_and_separates_construction(self):
        report = run_benchmark(self.args())
        self.assertEqual(report["fixture"]["result_lengths"], [6, 6])
        counts = report["operation_counts"]
        self.assertEqual(counts["index_build_input_items"], 7)
        self.assertEqual(counts["indexed_one_shot_membership_checks"], 12)
        self.assertEqual(counts["indexed_reuse_total_membership_checks"], 24)
        for path in ("indexed_one_shot", "index_build_only", "indexed_reuse_total", "indexed_reuse_queries_only"):
            self.assertEqual(len(report["timing"][path]["samples_ns"]), 2)


if __name__ == "__main__":
    unittest.main()
