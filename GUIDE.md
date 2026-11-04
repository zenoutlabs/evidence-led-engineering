# Evidence-Led Engineering

Help a coding agent make code faster without changing required behavior. Measure a representative workflow. Choose a small change. Verify correctness and the user-visible result.

This guide applies across languages. The examples use Python to make the method easy to run. Example timings are measurements of those examples on one environment. They are not forecasts for another project.

## 1. Choose the right amount of work

| Task | Useful action | Completion evidence |
| --- | --- | --- |
| Small edit with no suspected performance issue | Use a suitable algorithm and bounded work | Relevant existing checks; no unsupported speed claim |
| Slow workflow or substantial optimization | Measure a baseline, test one hypothesis, and compare | Equivalent outputs and repeatable workflow evidence |
| Rewrite, persistent cache, or operational change | Add resource, integration, failure, and rollback checks | Evidence that the benefit justifies the added cost |

Do not turn every small edit into an audit. Do not use a large input count alone to justify a new language.

## 2. Define success before changing code

State the user-visible endpoint. “The result appears within the target time” is more useful than “this function is faster.” Define what must remain true:

- Correct scope, output order, and duplicate behavior.
- Exact arithmetic, currency, and rounding rules where needed.
- Owner decisions and authorization.
- Cache validity, persistence, and failure recovery.
- Provider request size, rate, concurrency, and backoff rules.

Choose an acceptance rule that fits the project. Record input shape and environment. Keep the original implementation or a trusted reference for comparison. If the original behavior is wrong, use the required contract as the expected result.

## 3. Find where the time goes

Measure from the user's action to the correct result becoming visible. Separate:

1. CPU computation.
2. Database and file input/output (I/O).
3. Network latency.
4. Deliberate pacing and allowance waits.
5. The delay before the user interface (UI) shows the result.

Elapsed time includes waiting. Process CPU time measures a different quantity. Trace the boundaries that matter. Concurrent stages can overlap, so their durations cannot always be added.

Use a profiler to locate repeated or dominant work. Use separate repeated timings to measure speed. Python's profiler documentation explains why instrumentation can distort comparisons, especially across Python and native code. [Python profiling documentation](https://docs.python.org/3.13/library/profile.html).

Do not assume that two languages have equal file performance because they call the same operating system. Buffering and text conversion add work above those calls. This is a reason to measure the whole workflow, not a claim that one language is faster. [Python I/O documentation](https://docs.python.org/3.13/library/io.html#performance).

## 4. Remove the repeated work that the evidence shows

Useful candidates include:

| Repeated work | Candidate change | Behavior to protect |
| --- | --- | --- |
| Search the same list for each record | Build one scoped set or dictionary | Scope, duplicates, and left order |
| Fetch a whole table, then filter | Apply scoped predicates and inspect the query plan | Authorization, nulls, ordering, and pagination |
| Parse or assess the same input repeatedly | Reuse a stable result inside the operation | Inputs and owner decisions |
| Repeat a result across operations | Use a bounded version-bound cache | All dependencies and invalidation |
| Send or write one item at a time | Use a bounded batch | Caps, cancellation, latency, and failure behavior |
| Rewrite all state for a small change | Evaluate narrower updates or a log | Durability, recovery, and compaction cost |

Each change has a cost. An index uses memory and takes time to build. A cache can return an old answer. A batch can increase failure scope. A narrower write can complicate recovery. Test the relevant cost instead of assuming the pattern always helps.

## 5. Understand the membership example

Suppose records are identified by `(scope, item_id)`. The task is to remove each left record whose key occurs on the right. Keep every remaining left record in its original order, including duplicates.

```python
left = [("alpha", 2), ("alpha", 1), ("alpha", 2), ("beta", 1)]
right = [("alpha", 1)]
excluded = set(right)
result = [key for key in left if key not in excluded]
assert result == [("alpha", 2), ("alpha", 2), ("beta", 1)]
```

Let `n` be the number of left records and `m` the number of right records. Searching up to `m` keys for each left record can require O(n × m) work. Building a hash index and then filtering takes expected O(n + m) work under suitable hash distribution and bounded key costs. The index needs O(m) extra space. These are growth estimates, not speed guarantees. [CPython operation complexity](https://docs.python.org/3/builtins/time-complexity.html).

Two mistakes are easy to make. `set(left) - set(right)` can remove required duplicates and order. Matching only `item_id` can exclude a record from another scope. This operation is membership exclusion. It is not multiset subtraction, where each right occurrence removes only one left occurrence.

Not every nested loop is quadratic. A loop over groups and each group's own members visits the total member count. A loop over every possible pair does different work. State the dimensions and count visits before choosing a complexity label.

## 6. Run a fair comparison

From the repository folder:

```bash
python3 -m unittest discover -s tests -v
python3 skills/evidence-led-performance/scripts/performance_examples.py
python3 skills/evidence-led-performance/scripts/benchmark_membership.py
```

The benchmark uses a fixed seed and prints its parameters and fixture digest. The default fixture has 500 left records and 300 right records. Half of the left records match a right key. It reports five timed repetitions per path and three queries for the reuse scenario.

The report separates these questions:

- **One-shot use:** scan and produce output versus build an index and produce the same output.
- **Index construction:** the cost of building the index by itself.
- **Reuse:** repeated scans versus one index build and several queries.
- **Query-only reuse:** queries against an existing index. This excludes construction and must be labeled that way.

Output equality is checked outside each timed interval. The script alternates measurement order. It collects memory evidence in a separate run with `tracemalloc`. That measures traced Python allocations, not total process memory. [Python memory tracing documentation](https://docs.python.org/3.13/library/tracemalloc.html#tracemalloc.get_traced_memory).

Use a few bounded variations to test growth and hit rates:

```bash
python3 skills/evidence-led-performance/scripts/benchmark_membership.py --n 250 --m 100 --hit-rate 0 --repeats 3
python3 skills/evidence-led-performance/scripts/benchmark_membership.py --n 500 --m 100 --hit-rate 0.5 --repeats 3
python3 skills/evidence-led-performance/scripts/benchmark_membership.py --n 500 --m 400 --hit-rate 1 --repeats 3
```

The script rejects excessive workloads. Do not remove its limits to obtain a larger headline. For a real project, design a separate bounded experiment around its actual workload.

The initial sample is not a true cold-start measurement. Fixture construction and parity checks have already occurred. Warm samples also retain runtime and operating-system state. Name the cache layer being tested. Rebuilding an index does not flush a storage cache.

## 7. Verify the behavior that can change

The supplied tests cover empty inputs, all hits, misses, left duplicates, order, mixed scopes, and index rebuilds. They compare small exhaustive fixtures against the reference scan.

The cache example uses scope, record identity, data version, rules version, owner version, and an explicit owner decision. It caches negative results and bounds entry count. It also provides explicit invalidation. A writer must advance a version when its dependency changes. The example does not provide thread safety or durable storage.

The money example sums integer minor units in one currency. It rejects mixed currencies and non-integer amounts. Python's large integers do not prove that a fixed-width implementation cannot overflow.

The batch example preserves order and duplicates. It rejects a batch above the provider cap and checks cancellation before yielding the next batch. It sends no requests. A real dispatcher must still enforce current rate, concurrency, quota, and retry rules.

For changes to persisted state, test failures and recovery in a safe environment. Preserve transaction and flush requirements. Weaker synchronization can change durability, so it is not an equivalent performance comparison. [SQLite synchronization documentation](https://www.sqlite.org/pragma.html#pragma_synchronous).

## 8. Check whether the whole workflow improves

Amdahl's law bounds the benefit when only one part improves:

`whole-workflow speedup = 1 / ((1 - p) + p / s)`

`p` is the affected fraction of baseline elapsed time. `s` is the speedup of that part. If the part uses 30% of the time and becomes 10 times faster, the ideal whole-workflow speedup is about 1.37 times. The estimate assumes fixed work and unchanged remaining cost. [LLNL's explanation of Amdahl's law](https://hpc.llnl.gov/documentation/tutorials/introduction-parallel-computing-tutorial).

Measure the final workflow. Record memory, query count, bytes transferred, and write amplification when relevant. For write amplification, state the layer measured: application serialization, database writes, or device writes.

## 9. Consider a native component only when justified

A native component may help a remaining measured CPU bottleneck. Define a stable contract first. Include data transfer, copying, serialization, startup, errors, cancellation, and packaging in the comparison.

Use a small prototype. Check semantic parity and supported platforms. Compare the end-to-end benefit with the build and maintenance cost. A native component cannot remove a required provider wait just by running CPU instructions faster.

## Requests to give your coding agent

**For a small edit:**

```text
Apply the Evidence-Led Engineering method in proportion to this change.
Use a suitable data structure and preserve behavior.
Run the relevant checks. Do not claim a speedup without measurements.
```

**For a slow workflow:**

```text
Measure this workflow from request to correct result visible.
Separate computation, I/O, network, pacing, allowance waits, and UI delay.
Test one supported optimization. Keep the same scope and operational rules.
Return behavior checks, comparable timings, resource effects, and limits.
```

**For a proposed rewrite:**

```text
Evaluate this rewrite against the measured bottleneck.
First check algorithms, data structures, repeated work, and scoped queries.
Include the likely workflow benefit and the integration cost.
Recommend a small reversible change when the evidence supports it.
```

See the skill's [measurement reference](skills/evidence-led-performance/references/measurement.md) for an evidence record, [semantic contracts](skills/evidence-led-performance/references/semantic-contracts.md) for deeper checks, and [technical sources](skills/evidence-led-performance/references/sources.md) for the primary references.
