# Design a useful measurement

Read this when a slowdown, substantial optimization, or proposed rewrite needs evidence. Use only the parts that fit the task.

## Define the outcome

Use a user-visible endpoint, such as “request accepted to correct result visible.” State the target and why it matters. Define where timing starts and ends. A fast background job with a stale screen is still a slow user experience.

Before coding, record:

- The input and output contract, including failure behavior.
- The baseline revision, candidate revision, runtime, build mode, and environment.
- The fixture seed or digest, data shape, input sizes, hit rate, duplicate rate, and skew.
- The workload bound, stopping conditions, relevant resource budget, and behavior checks.
- The acceptance rule. It can be a latency budget or a repeatable reduction larger than observed noise. Choose it before seeing favorable results.

Use representative synthetic or approved sanitized fixtures. Keep private source data out of shared artifacts. Preserve distribution and difficult cases when sanitizing.

## Separate the causes

| Category | Useful evidence | Likely next step |
| --- | --- | --- |
| CPU computation | Sampled stacks, function calls, process CPU time | Reduce repeated computation or allocations |
| Database work | Query count, rows read/returned, query plan, lock waits | Scope queries, change access paths, test an index |
| File input/output (I/O) | Read/write calls, bytes, parse time, flush policy | Reduce repeated parsing or writes; preserve durability |
| Network | Trace spans, payload bytes, connection and server time | Bound requests; batch within provider rules |
| Pacing or allowance wait | Explicit wait spans, retry reasons, quota state | Improve scheduling only within the existing rules |
| UI freshness | Result committed, event delivered, render completed | Fix notification, refresh, or rendering delay |

Wall time includes waiting. Process CPU time usually does not. Their difference alone does not identify the kind of wait. Instrument the relevant boundaries. Concurrent spans overlap; do not add their durations as if they ran in sequence. Attribute the critical path to the visible outcome.

## Locate work, then measure speed

Profilers identify where time or calls accumulate. They can distort the program. Measure baseline and candidate separately without profiler instrumentation. Do not use a profiler's Python-versus-native timing as proof of a language advantage.

For a bounded local test:

1. Prepare the same fixture for both implementations.
2. Check output equality before timing.
3. Run a small warm-up when it matches the intended steady state.
4. Alternate baseline-first and candidate-first trials, or randomize with a recorded seed.
5. Retain raw times and report a summary plus spread.
6. Run memory checks separately from timing.
7. Repeat the real workflow check after the change.

Do not select only the best candidate run. Small sample maxima are not reliable tail-latency estimates. Record noise from competing work, thermal changes, garbage collection, runtime compilation, and caches when relevant. Python's `timeit` normally excludes setup and disables garbage collection. Those defaults can omit real work; configure them deliberately.

## Compare equivalent work

Keep these conditions equal, or report the difference:

- Inputs, scope, ordering, duplicate rules, output materialization, and exact arithmetic.
- Build mode, runtime, worker count, concurrency, retry policy, and provider caps.
- Persistence, transaction boundaries, flushing, errors, and cancellation behavior.
- Cache state, data versions, and index construction.

For one query, compare `scan + output` with `index build + indexed query + output`. For many queries, report construction, query-only time, number of reuses, and total time. Invalidate or rebuild when the indexed data changes. A fictional perfectly reused index does not establish a production gain.

## Cold, warm, and scale

Define “cold” precisely. It may mean a fresh process, an empty application cache, an absent index, or a storage cache miss. Rebuilding a set does not flush the operating system's file cache. Do not reset shared system caches during live work just to improve an experiment.

Test multiple relevant sizes. Vary n and m independently where possible. For membership work, vary hit rate and hit position. Record operation counts separately from timings. Counts can expose growth even when short timings are noisy.

Include memory, allocation pressure, query counts, bytes transferred, and write amplification when they can change the decision. Write amplification is the amount written compared with the logical change. State the layer measured; serialized application bytes are not physical device writes. Python `tracemalloc` measures traced Python allocations, not total process resident memory (RSS), database cache size, or device traffic.

## Estimate the maximum benefit

Amdahl's law gives an idealized speedup:

`S = 1 / ((1 - p) + p / s)`

Here, `p` is the measured fraction of baseline time affected by the change. `s` is the speedup of that part. If 30% of a sequential workflow becomes 10 times faster, `S = 1 / (0.70 + 0.03)`, or about 1.37 times. Even infinite speed in that part gives at most about 1.43 times.

This estimate assumes unchanged work elsewhere and no new overhead. Concurrency, queueing, cache effects, and a changed workload can violate that model. Use a measured critical-path fraction where stages overlap. Confirm the final outcome with end-to-end measurement.

## Minimal evidence record

```text
Outcome and acceptance rule:
Baseline / candidate revisions:
Environment and runtime:
Fixture, seed or digest, n, m, distributions:
Scope and semantic invariants:
Timing boundaries and overlapping stages:
Cold / warm definitions:
Repeated raw results and summary:
Operation counts and relevant resources:
Behavior checks and workflow checks:
Limits, uncertainty, rollout and rollback:
```

The bundled benchmark fills part of this record for an in-memory illustration. It is not an application benchmark. See [sources.md](sources.md) for measurement documentation.
