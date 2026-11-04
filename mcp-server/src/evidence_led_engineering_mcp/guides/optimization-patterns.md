# Choose a change from evidence

Read only the pattern relevant to the measured work. These are candidate changes, not a universal checklist.

## Membership and indexed lookup

Let `n` be the number of left records and `m` the number of right keys. A scan that searches all right keys for each left record can require `n × m` equality comparisons. Early matches reduce actual work. Record the hit rate and match position.

A hash index builds the right-key set once, then checks each left record. Under suitable hash distribution and bounded hash/equality cost, this is expected O(n + m) time and O(m) extra space in the worst case of all unique right keys. Hash collisions and expensive keys can make it worse. These assumptions apply to the chosen implementation, not all languages or all key types.

Keep the left sequence and test membership against the right index. Converting both inputs to sets can remove duplicates and order. Include scope in the key when IDs are only unique within an owner or tenant.

Not every nested loop is quadratic. A loop over groups and their own members visits the total member count. A merge over two sorted sequences can be O(n + m). A loop over all pairs is O(n × m); calling it O(n²) assumes both dimensions grow together. Choose a sorted merge, hash index, or database operation based on the contract and resource limits.

Index construction can dominate tiny or one-shot work. A persistent or reused index adds invalidation and memory costs. Measure the real reuse rate, including rebuilds.

## Scoped queries and database indexes

Reduce rows and columns before moving data into the application. Include the required scope and predicates. Inspect the query plan on representative data. An index can reduce reads but adds storage and write work. Key order, selectivity, sort requirements, and the database engine matter.

Compare rows examined, rows returned, query count, elapsed time, lock waits, and write overhead where relevant. Avoid one query per record when a bounded set-based query can preserve the result. Preserve null handling, duplicates, authorization, pagination, and explicit ordering. Do not assume a database returns stable order without an ordering contract.

## Repeated computation and caching

First remove accidental duplicate work within one operation. Parse once, compute once, and pass a stable result when feasible. This often has a smaller correctness cost than a long-lived cache.

Use a version-bound cache when repeated results justify it. Include scope, data version, rules, and owner decisions in the cache identity. Define invalidation and memory bounds. Measure misses, hits, rebuilds, and realistic reuse. See [semantic-contracts.md](semantic-contracts.md).

## Batching and persistence

Batch bounded work to reduce per-item overhead. Keep memory, latency, cancellation, transaction size, provider caps, and failure behavior within the contract. Avoid a batch that prevents useful progress or hides a partial failure.

If a one-record update rewrites a complete state file, measure serialized bytes, bytes submitted for writing, flush time, and recovery behavior. A narrower update or append log may reduce writes but introduces compaction, recovery, and consistency costs. Do not change durability just to improve timing.

## File I/O and language claims

Languages can reach the same operating-system interface and still have different elapsed times. Buffer sizes, call counts, encoding, parsing, allocations, copying, runtime overhead, filesystem state, page caches, and synchronization behavior can differ. Compare the full read-parse-process-write workflow with equivalent outputs and durability.

Do not infer equal I/O time from a shared kernel call. Do not infer that a language rewrite will fix a workload dominated by network waits or provider pacing.

## A native component

Consider a compiled or native-language component only after measuring a remaining bottleneck. Evaluate:

- The measured CPU fraction and the likely end-to-end benefit.
- A stable input/output contract, including errors, cancellation, ordering, and exact arithmetic.
- Transfer, serialization, copying, allocation, and startup costs at the real batch size.
- Build, packaging, deployment, debugging, observability, security, and maintenance cost.
- Differential tests, resource behavior, supported platforms, and a rollback path.

Prototype a small boundary before a rewrite. Compare equivalent work outside the profiler. Use [measurement.md](measurement.md) for Amdahl's law and the experiment record. Keep the current implementation when the evidence does not justify the integration cost.
