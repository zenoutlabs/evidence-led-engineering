"""Bounded, synthetic membership benchmark. Results are not project forecasts.

Run from this skill directory:
  python3 scripts/benchmark_membership.py --n 500 --m 300 --hit-rate 0.5

JSON goes to stdout. Save it with shell redirection if needed. This script uses
no network, changes no provider limits, and writes no files by itself.

The full run permits at most 40,000,000 worst-case scan key comparisons.
This ceiling includes baselines, initial samples, warm-up, timed repetitions,
memory samples, and operation counting. Actual counts can be lower after hits.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import platform
import random
import statistics
import sys
import time
import tracemalloc
from collections.abc import Callable

from performance_examples import Item, build_index, difference_indexed, difference_scan, difference_with_index


MAX_SCAN_COMPARISONS = 40_000_000


def make_fixture(n: int, m: int, hit_rate: float, seed: int, queries: int):
    right = [Item(f"scope-{i % 3}", i, 100 + i % 97) for i in range(m)]
    hit_count = round(n * hit_rate)
    workloads = []
    for query in range(queries):
        rng = random.Random(seed + query)
        hits = [rng.choice(right) for _ in range(hit_count)]
        misses = [Item(f"scope-{i % 3}", m + i, 100 + rng.randrange(97)) for i in range(n - hit_count)]
        left = hits + misses
        rng.shuffle(left)
        workloads.append(left)
    return right, workloads


def scan_comparisons(left, right) -> int:
    """Count key equality checks separately from timed code."""
    count = 0
    for item in left:
        for excluded in right:
            count += 1
            if item.key == excluded.key:
                break
    return count


def timed_call(call: Callable):
    start = time.perf_counter_ns()
    result = call()
    elapsed = time.perf_counter_ns() - start
    return elapsed, result


def allocation_peak(call: Callable) -> int:
    """Peak traced Python allocations in one call, including its live result."""
    tracemalloc.start()
    try:
        result = call()
        _, peak = tracemalloc.get_traced_memory()
        # Keep result live until after the sample.
        del result
        return peak
    finally:
        tracemalloc.stop()


def validate_arguments(parser, args):
    if not 0 <= args.n <= 5_000 or not 0 <= args.m <= 5_000:
        parser.error("n and m must be from 0 to 5000")
    if not math.isfinite(args.hit_rate) or not 0 <= args.hit_rate <= 1:
        parser.error("hit-rate must be finite and from 0 to 1")
    if args.m == 0 and round(args.n * args.hit_rate):
        parser.error("a nonzero hit count requires m > 0")
    if not 1 <= args.repeats <= 9 or not 1 <= args.reuse_queries <= 8:
        parser.error("repeats must be 1..9; reuse-queries must be 1..8")
    # Baselines, initial samples, warm-up, and memory sampling each run both
    # scan paths once. Timed repetitions run both paths repeatedly. Operation
    # counting runs each reused workload once more. Every scan can compare
    # all n left keys with all m right keys when there are no matches.
    scan_invocations = (args.repeats + 4) * (1 + args.reuse_queries) + args.reuse_queries
    if args.n * args.m * scan_invocations > MAX_SCAN_COMPARISONS:
        parser.error("full-run scan work exceeds 40000000 key comparisons; reduce n, m, repeats, or reuse-queries")
    if not -(2**31) <= args.seed < 2**31:
        parser.error("seed must fit a signed 32-bit integer")


def run_benchmark(args) -> dict:
    right, workloads = make_fixture(args.n, args.m, args.hit_rate, args.seed, args.reuse_queries)
    left = workloads[0]
    prebuilt = build_index(right)
    expected_one = difference_scan(left, right)
    expected_reuse = [difference_scan(query, right) for query in workloads]

    def indexed_reuse_total():
        index = build_index(right)
        return [difference_with_index(query, index) for query in workloads]

    calls = {
        "scan_one_shot": lambda: difference_scan(left, right),
        "indexed_one_shot": lambda: difference_indexed(left, right),
        "index_build_only": lambda: build_index(right),
        "scan_reuse_total": lambda: [difference_scan(query, right) for query in workloads],
        "indexed_reuse_total": indexed_reuse_total,
        "indexed_reuse_queries_only": lambda: [difference_with_index(query, prebuilt) for query in workloads],
    }
    expected = {
        "scan_one_shot": expected_one,
        "indexed_one_shot": expected_one,
        "index_build_only": prebuilt,
        "scan_reuse_total": expected_reuse,
        "indexed_reuse_total": expected_reuse,
        "indexed_reuse_queries_only": expected_reuse,
    }
    initial = {}
    for name, call in calls.items():
        elapsed, result = timed_call(call)
        if result != expected[name]:
            raise AssertionError(f"output mismatch: {name}")
        initial[name] = elapsed
    for call in calls.values():
        call()  # One unmeasured warm-up per path.

    samples = {name: [] for name in calls}
    names = list(calls)
    for repeat in range(args.repeats):
        # Alternate the direction to reduce consistent first/last bias.
        order = names if repeat % 2 == 0 else list(reversed(names))
        for name in order:
            elapsed, result = timed_call(calls[name])
            if result != expected[name]:
                raise AssertionError(f"output mismatch: {name}")
            samples[name].append(elapsed)

    timing = {}
    for name, values in samples.items():
        timing[name] = {
            "samples_ns": values,
            "median_ns": statistics.median(values),
            "minimum_ns": min(values),
            "maximum_ns": max(values),
            "initial_timed_ns": initial[name],
        }
    memory = {name: allocation_peak(call) for name, call in calls.items()}
    fixture_rows = [[(x.scope, x.item_id, x.amount_minor, x.currency) for x in query] for query in [right, *workloads]]
    fingerprint = hashlib.sha256(json.dumps(fixture_rows, separators=(",", ":")).encode()).hexdigest()
    scan_counts = [scan_comparisons(query, right) for query in workloads]
    return {
        "schema_version": 1,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "gc_enabled": gc.isenabled(),
            "clock": "perf_counter_ns",
            "clock_resolution_seconds": time.get_clock_info("perf_counter").resolution,
        },
        "parameters": vars(args),
        "fixture": {
            "sha256": fingerprint,
            "actual_hits_per_query": round(args.n * args.hit_rate),
            "actual_hit_rate": round(args.n * args.hit_rate) / args.n if args.n else 0.0,
            "right_distinct_scoped_keys": len(prebuilt),
            "result_lengths": [len(result) for result in expected_reuse],
        },
        "correctness": "all timed results equal the scan baseline",
        "timing": timing,
        "operation_counts": {
            "scan_one_shot_key_comparisons": scan_counts[0],
            "scan_reuse_total_key_comparisons": sum(scan_counts),
            "index_build_input_items": args.m,
            "indexed_one_shot_membership_checks": args.n,
            "indexed_reuse_total_membership_checks": args.n * args.reuse_queries,
            "note": "Counts are logical operations, not hash probes, CPU instructions, or equal-cost units.",
        },
        "memory_peak_traced_python_bytes": memory,
        "limitations": [
            "Synthetic in-memory workload; no project speedup is implied.",
            "Initial timed samples follow fixture construction and parity checks; they are not cold-start or cold-cache measurements.",
            "Repeated samples follow one warm-up. CPU frequency, background load, allocator state, and OS caches are uncontrolled.",
            "One-shot indexed timing includes index construction. Reuse-total timing includes one construction for all queries.",
            "Queries-only timing excludes index construction and is not a fair standalone replacement for one-shot timing.",
            "Memory is sampled separately with tracemalloc. It is Python allocation peak, not process RSS or total memory.",
            "Queries-only memory excludes the prebuilt index. Index-build memory is reported separately; peaks cannot simply be added.",
            "No database, file I/O, network, pacing, durability, or UI behavior is measured.",
            "No timing threshold is used to pass or fail this example.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=500, help="left items per query, 0..5000")
    parser.add_argument("--m", type=int, default=300, help="right items, 0..5000")
    parser.add_argument("--hit-rate", type=float, default=0.5, help="fraction of left items with a right key, 0..1")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--repeats", type=int, default=5, help="timed samples per path, 1..9")
    parser.add_argument("--reuse-queries", type=int, default=3, help="queries per reused index, 1..8")
    args = parser.parse_args()
    validate_arguments(parser, args)
    print(json.dumps(run_benchmark(args), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
