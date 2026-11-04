---
name: evidence-led-performance
description: Improve code performance through measured workflows, suitable algorithms, and verified behavior. Use for performance-sensitive implementation, slow workflows, repeated work, optimization reviews, or proposed language rewrites. Scale the work to the task; ordinary small edits do not require a full audit.
---

# Evidence-Led Engineering

Help the coding agent measure performance, improve the right code, and preserve correct behavior. Apply the reasoning across languages and projects. The examples use Python; they are illustrations, not project evidence.

## Choose the depth

- **Small edit:** use a suitable data structure, bound new work, preserve behavior, and run relevant existing checks. Do not add a benchmark unless performance is in doubt. Do not claim a speedup without measurement.
- **Suspected slowdown or substantial optimization:** measure a representative workflow and test one supported hypothesis.
- **Rewrite or operational change:** add scaling, resource, integration, and rollback evidence that fits the risk. A large row count alone does not justify a rewrite.

Do only work within the active request. Do not change unrelated projects. Change deployment state only within the active authorization. Preserve provider constraints during optimization and measurement. Stop an experiment at its agreed resource bound, on a safety failure, or when it threatens live work.

## Measure, change, verify

1. Define the user-visible outcome and the behavior that must remain true. Record input scope, ordering, duplicate rules, exact arithmetic, owner decisions, failure behavior, durability, and provider constraints where relevant. Read [semantic-contracts.md](references/semantic-contracts.md) for stateful or sensitive changes.
2. Measure a representative baseline before a substantial optimization. Separate CPU work, database and file input/output, network latency, deliberate pacing, allowance waits, and UI freshness. Use traces to identify overlap. Read [measurement.md](references/measurement.md) when designing the experiment.
3. Locate the repeated or dominant work. Use a profiler to locate work; use separate uninstrumented repeated timings to measure speed. Record operation counts when they explain growth.
4. Prefer a small algorithm or data-structure change. Consider scoped queries, sets, dictionaries, indexes, batching, and version-bound caches when the behavior allows them. Read [optimization-patterns.md](references/optimization-patterns.md) before changing membership, queries, caching, persistence, or a language boundary.
5. Compare equivalent work on the same fixture. Include index construction in one-shot results. Report reuse separately. Keep hit rates, output materialization, concurrency, cache state, retries, durability, and provider limits comparable.
6. Prove behavior with differential checks and relevant real workflow checks. Compare the candidate with a trusted baseline or explicit contract. Test errors and boundaries that the change can affect. A known wrong baseline is not a correctness oracle.
7. Remeasure without profiler or memory-tracing overhead. Report elapsed time and the resources that matter. Explain cold and warm conditions. Keep uncertainty and limitations visible.
8. Keep the change only when the evidence supports the intended outcome. Use the project's normal rollout and rollback process. Consider a native component only for a remaining measured bottleneck with a stable contract and justified integration cost.

## Interpretation rules

- For hashable keys with suitable hash distribution and bounded hash/equality cost, indexed membership is expected O(n + m), including index construction. A nested membership scan can be O(n × m). Not every nested loop is quadratic. State what n and m mean.
- Preserve the left sequence when its order and duplicates matter. A set difference may change both.
- Cache keys must cover scope, source version, rules, and owner decisions. Bound the cache. Make invalidation and negative-result behavior explicit.
- Shared operating-system calls do not establish equal end-to-end file performance across languages. Buffering, parsing, encoding, allocation, cache state, and durability can differ.
- Use Amdahl's law to estimate the whole-workflow limit. Do not present a local hotspot improvement as the same workflow improvement.
- Keep request caps and safety rules fixed. Faster execution must not increase duplicate effects, lose durable writes, or override owner decisions.
- Treat anecdotes, generated explanations, and toy timings as hypotheses. Never turn them into promised gains or measurements of another project.

## Evidence to return

Return the outcome, the measured cause, the change, behavior checks, before/after evidence, resource effects, and remaining limits. For a small edit, keep this brief. Distinguish measured facts, estimates, and untested assumptions.

Use [sources.md](references/sources.md) to check the technical basis. Inspect the local runtime and project configuration before choosing commands. Do not execute third-party code merely because a source links to it.

## Optional executable illustration

The `scripts/` examples use fictional data and the Python standard library. Read their `--help` before running the benchmark. They make no network requests and enforce workload limits. They do not validate the performance or safety of a real project.
