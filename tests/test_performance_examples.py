"""Deterministic behavior checks. Timing is not a pass/fail condition."""

import itertools
from pathlib import Path
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills/evidence-led-performance/scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from performance_examples import (  # noqa: E402
    AssessmentCache,
    AssessmentKey,
    Item,
    bounded_batches,
    build_index,
    difference_indexed,
    difference_scan,
    difference_with_index,
    total_minor_units,
)


class DifferenceTests(unittest.TestCase):
    def test_empty_and_all_hit_inputs(self):
        item = Item("alpha", 1)
        self.assertEqual(difference_indexed([], [item]), [])
        self.assertEqual(difference_indexed([item], []), [item])
        self.assertEqual(difference_indexed([item, item], [item]), [])

    def test_order_duplicates_and_scope_are_preserved(self):
        first = Item("alpha", 2, 100)
        second = Item("alpha", 1, 201)
        same_id_other_scope = Item("beta", 1, 300)
        left = [first, second, first, same_id_other_scope]
        right = [Item("alpha", 1, 999), Item("alpha", 1, 999)]
        result = difference_indexed(left, right)
        self.assertEqual(result, [first, first, same_id_other_scope])
        self.assertIs(result[0], first)
        self.assertEqual(left, [first, second, first, same_id_other_scope])

    def test_membership_exclusion_is_not_multiset_subtraction(self):
        item = Item("alpha", 1)
        self.assertEqual(difference_indexed([item, item], [item]), [])

    def test_exhaustive_small_fixtures_match_baseline(self):
        alphabet = (Item("alpha", 1, 100), Item("alpha", 2, 200), Item("beta", 1, 300))
        sequences = [list(values) for size in range(4) for values in itertools.product(alphabet, repeat=size)]
        for left in sequences:
            for right in sequences:
                with self.subTest(left=left, right=right):
                    self.assertEqual(difference_indexed(left, right), difference_scan(left, right))

    def test_reused_index_requires_rebuild_after_source_change(self):
        left = [Item("alpha", 1), Item("alpha", 2)]
        right = [left[0]]
        old_index = build_index(right)
        right.append(left[1])
        self.assertEqual(difference_with_index(left, old_index), [left[1]])
        self.assertEqual(difference_with_index(left, build_index(right)), [])


class CacheTests(unittest.TestCase):
    def key(self, **changes):
        values = dict(scope="alpha", item_id=1, data_version=1, rule_version=1, owner_version=1)
        values.update(changes)
        return AssessmentKey(**values)

    def test_false_and_none_are_cached(self):
        for result in (False, None):
            cache = AssessmentCache()
            calls = []

            def compute():
                calls.append(1)
                return result

            self.assertIs(cache.get_or_compute(self.key(), compute), result)
            self.assertIs(cache.get_or_compute(self.key(), compute), result)
            self.assertEqual(len(calls), 1)

    def test_each_dependency_version_and_scope_separates_entries(self):
        cache = AssessmentCache()
        cache.get_or_compute(self.key(), lambda: False)
        for changes in ({"data_version": 2}, {"rule_version": 2}, {"owner_version": 2}, {"scope": "beta"}, {"item_id": 2}):
            self.assertIs(cache.get_or_compute(self.key(**changes), lambda: True), True)
        self.assertIs(cache.get_or_compute(self.key(), lambda: True), False)

    def test_owner_override_wins_and_change_does_not_reuse_old_result(self):
        cache = AssessmentCache()

        def must_not_compute():
            self.fail("an explicit owner decision must take priority")

        self.assertIs(cache.get_or_compute(self.key(owner_decision=False), must_not_compute), False)
        self.assertIs(cache.get_or_compute(self.key(owner_decision=True), must_not_compute), True)
        self.assertIs(cache.get_or_compute(self.key(owner_version=2), lambda: None), None)

    def test_explicit_invalidation_keeps_other_scopes(self):
        cache = AssessmentCache()
        cache.get_or_compute(self.key(), lambda: False)
        cache.get_or_compute(self.key(scope="beta"), lambda: False)
        cache.invalidate_scope("alpha")
        self.assertEqual(len(cache), 1)
        self.assertIs(cache.get_or_compute(self.key(), lambda: True), True)
        self.assertIs(cache.get_or_compute(self.key(scope="beta"), lambda: True), False)
        cache.clear()
        self.assertEqual(len(cache), 0)

    def test_cache_bound_and_recent_use(self):
        cache = AssessmentCache(max_entries=2)
        cache.get_or_compute(self.key(item_id=1), lambda: False)
        cache.get_or_compute(self.key(item_id=2), lambda: False)
        cache.get_or_compute(self.key(item_id=1), lambda: True)
        cache.get_or_compute(self.key(item_id=3), lambda: False)
        self.assertEqual(len(cache), 2)
        self.assertIs(cache.get_or_compute(self.key(item_id=1), lambda: True), False)
        self.assertIs(cache.get_or_compute(self.key(item_id=2), lambda: True), True)

    def test_failures_are_not_cached(self):
        cache = AssessmentCache()
        with self.assertRaises(RuntimeError):
            cache.get_or_compute(self.key(), lambda: (_ for _ in ()).throw(RuntimeError("failed")))
        self.assertEqual(len(cache), 0)
        self.assertIs(cache.get_or_compute(self.key(), lambda: True), True)

    def test_mutable_or_non_boolean_results_are_rejected(self):
        cache = AssessmentCache()
        for value in ([], 1, "yes"):
            with self.assertRaises(TypeError):
                cache.get_or_compute(self.key(), lambda: value)
        self.assertEqual(len(cache), 0)

    def test_invalid_cache_capacity_is_rejected(self):
        for capacity in (0, -1, 10001, True):
            with self.assertRaises(ValueError):
                AssessmentCache(capacity)


class MoneyAndBatchTests(unittest.TestCase):
    def test_large_money_and_negative_adjustment_are_exact(self):
        items = [Item("alpha", 1, 10**30), Item("alpha", 2, 101), Item("alpha", 3, -2)]
        self.assertEqual(total_minor_units(items, "USD"), 10**30 + 99)
        self.assertEqual(total_minor_units([], "JPY"), 0)

    def test_currency_and_non_integer_money_are_rejected(self):
        with self.assertRaises(ValueError):
            total_minor_units([Item("alpha", 1, 100, "EUR")], "USD")
        for amount in (1.01, True, "100"):
            with self.assertRaises(TypeError):
                total_minor_units([Item("alpha", 1, amount)], "USD")

    def test_batches_preserve_duplicates_order_and_cap(self):
        items = [3, 1, 3, 2, 4]
        batches = list(bounded_batches(items, batch_size=2, provider_cap=2))
        self.assertEqual(batches, [(3, 1), (3, 2), (4,)])
        self.assertEqual(list(bounded_batches([], 2, 2)), [])

    def test_invalid_batch_sizes_and_example_bound_are_rejected(self):
        for size, cap in ((3, 2), (0, 2), (2, 0), (1001, 2000), (True, 2)):
            with self.assertRaises(ValueError):
                list(bounded_batches([1, 2, 3], size, cap))
        with self.assertRaises(ValueError):
            list(bounded_batches(range(100001), 1000, 1000))

    def test_cancelled_work_produces_no_batch(self):
        self.assertEqual(list(bounded_batches([1, 2], 1, 1, lambda: True)), [])

    def test_cancellation_stops_future_batches(self):
        cancelled = False
        batches = bounded_batches([1, 2, 3], 1, 1, lambda: cancelled)
        self.assertEqual(next(batches), (1,))
        cancelled = True
        self.assertEqual(list(batches), [])


if __name__ == "__main__":
    unittest.main()
