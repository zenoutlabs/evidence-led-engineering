"""Small, local examples for evidence-led performance work.

No function sends a request or changes a file. The data is fictional.
Run these commands from the package root:
  python3 skills/evidence-led-performance/scripts/performance_examples.py
  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Iterator, Sequence, TypeVar


@dataclass(frozen=True)
class Item:
    scope: str
    item_id: int
    amount_minor: int = 0
    currency: str = "USD"

    @property
    def key(self) -> tuple[str, int]:
        return self.scope, self.item_id


def difference_scan(left: Sequence[Item], right: Sequence[Item]) -> list[Item]:
    """Remove every left item whose scoped key occurs in right.

    Keep the remaining left objects, their order, and their duplicates.
    This is membership exclusion, not multiset subtraction.
    """
    result = []
    for item in left:
        key = item.key
        for excluded in right:
            if key == excluded.key:
                break
        else:
            result.append(item)
    return result


def build_index(right: Sequence[Item]) -> set[tuple[str, int]]:
    return {item.key for item in right}


def difference_with_index(
    left: Sequence[Item], excluded_keys: set[tuple[str, int]]
) -> list[Item]:
    """The caller owns the index lifetime and must rebuild it after changes."""
    return [item for item in left if item.key not in excluded_keys]


def difference_indexed(left: Sequence[Item], right: Sequence[Item]) -> list[Item]:
    """Include index construction in the one-shot operation."""
    return difference_with_index(left, build_index(right))


@dataclass(frozen=True)
class AssessmentKey:
    """Identity plus every version that can change an assessment.

    A version must identify an immutable snapshot. The caller must advance
    data_version, rule_version, or owner_version when that dependency changes.
    Scope is required. A version value alone is not a global identity.
    """

    scope: str
    item_id: int
    data_version: int
    rule_version: int
    owner_version: int
    owner_decision: bool | None = None


class AssessmentCache:
    """Bounded, process-local cache for immutable bool/None assessments.

    False and None are valid cached results. Exceptions are not cached.
    An explicit owner decision takes priority over computed rules.
    This example has no thread synchronization or persistent storage.
    """

    def __init__(self, max_entries: int = 128) -> None:
        if type(max_entries) is not int or not 1 <= max_entries <= 10_000:
            raise ValueError("max_entries must be an integer from 1 to 10000")
        self.max_entries = max_entries
        self._entries: OrderedDict[AssessmentKey, bool | None] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def get_or_compute(
        self, key: AssessmentKey, compute: Callable[[], bool | None]
    ) -> bool | None:
        if key in self._entries:
            self._entries.move_to_end(key)
            return self._entries[key]
        result = key.owner_decision if key.owner_decision is not None else compute()
        if result is not None and type(result) is not bool:
            raise TypeError("an assessment must be bool or None")
        self._entries[key] = result
        if len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)
        return result

    def invalidate_scope(self, scope: str) -> None:
        """Remove obsolete entries when a scope changes or is no longer used."""
        for key in tuple(self._entries):
            if key.scope == scope:
                del self._entries[key]

    def clear(self) -> None:
        self._entries.clear()


def total_minor_units(items: Sequence[Item], currency: str) -> int:
    """Sum integer minor units in one currency, including negative adjustments.

    Currency conversion and decimal parsing belong at a defined input boundary.
    This function does not assume that all currencies have two decimal places.
    """
    total = 0
    for item in items:
        if item.currency != currency:
            raise ValueError("currency mismatch")
        if type(item.amount_minor) is not int:
            raise TypeError("amount_minor must be an integer")
        total += item.amount_minor
    return total


T = TypeVar("T")


def bounded_batches(
    items: Sequence[T],
    batch_size: int,
    provider_cap: int,
    cancelled: Callable[[], bool] = lambda: False,
) -> Iterator[tuple[T, ...]]:
    """Plan bounded batches without dispatching requests.

    Reject an oversized batch; do not raise or bypass the provider cap.
    Check cancellation before each batch. The caller must check cancellation,
    the current provider cap, and pacing again immediately before real dispatch.
    A cap on batch size does not define a request rate or concurrency limit.
    """
    if type(provider_cap) is not int or provider_cap < 1:
        raise ValueError("provider_cap must be a positive integer")
    if type(batch_size) is not int or not 1 <= batch_size <= 1_000:
        raise ValueError("batch_size must be an integer from 1 to 1000")
    if batch_size > provider_cap:
        raise ValueError("batch_size exceeds provider_cap")
    if len(items) > 100_000:
        raise ValueError("this example accepts at most 100000 items")
    for start in range(0, len(items), batch_size):
        if cancelled():
            return
        yield tuple(items[start : start + batch_size])


def main() -> None:
    left = [Item("alpha", 1, 101), Item("alpha", 1, 101), Item("beta", 1, -2)]
    right = [Item("beta", 1)]
    remaining = difference_indexed(left, right)
    assert remaining == difference_scan(left, right)
    print("Remaining scoped keys:", [item.key for item in remaining])
    print("Exact total in USD minor units:", total_minor_units(remaining, "USD"))
    print("Batch lengths:", [len(batch) for batch in bounded_batches(remaining, 1, 2)])


if __name__ == "__main__":
    main()
