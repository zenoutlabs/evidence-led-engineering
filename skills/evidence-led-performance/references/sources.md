# Technical sources

Checked on 2026-11-01. These primary sources support the method. The explanations in this package are independently written. Runtime details can change; check the documentation for the version in the target project.

| Source | What it supports | Qualification |
| --- | --- | --- |
| [Python built-in types, 3.13](https://docs.python.org/3.13/library/stdtypes.html#set-types-set-frozenset) | Sets store distinct hashable values. Sets do not preserve insertion order. Dictionaries preserve insertion order. | A set is useful as a membership index. It does not preserve all list semantics. |
| [CPython operation complexity](https://docs.python.org/3/builtins/time-complexity.html) | Average constant-time hash lookup under stated assumptions; collision and key-cost limits. | Implementation-specific. It does not establish a universal language guarantee. |
| [Python profilers, 3.13](https://docs.python.org/3.13/library/profile.html) | Profilers locate work. Instrumentation can distort speed comparisons, including Python versus C. | Use separate benchmark timings. |
| [Python timeit, 3.13](https://docs.python.org/3.13/library/timeit.html) | Repeated timing, excluded setup, and the default garbage-collection policy. | Include real index construction in one-shot work. |
| [Python time clocks, 3.13](https://docs.python.org/3.13/library/time.html#time.perf_counter_ns) | Elapsed time and process CPU time measure different things. | Nanosecond units do not imply nanosecond resolution. |
| [Python tracemalloc, 3.13](https://docs.python.org/3.13/library/tracemalloc.html#tracemalloc.get_traced_memory) | Current and peak traced Python allocations. | Not total resident memory or all native allocations. |
| [Python stream I/O, 3.13](https://docs.python.org/3.13/library/io.html#performance) | Buffering and text conversion add work above low-level I/O. | Different end-to-end file performance across languages is an inference from these layers, not a cross-language benchmark. |
| [SQLite query planning](https://www.sqlite.org/queryplanner.html) | Search, multi-column indexes, covering indexes, and sorting. | Test the actual engine, predicates, data, and write cost. |
| [SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) | Query-plan evidence for scans, searches, indexes, and temporary sorting. | Plan text can change. An index name alone does not prove a narrow search. |
| [SQLite synchronization settings](https://www.sqlite.org/pragma.html#pragma_synchronous) and [atomic commit](https://www.sqlite.org/atomiccommit.html) | Flush and synchronization choices affect durability and commit work. | Keep journal mode and durability guarantees comparable. |
| [LLNL introduction to parallel computing](https://hpc.llnl.gov/documentation/tutorials/introduction-parallel-computing-tutorial) | Amdahl's law limits whole-program benefit when only part improves. | The general-optimization formula in this package is an algebraic adaptation of the fixed-work model. |
| [Linux kernel cache controls](https://docs.kernel.org/admin-guide/sysctl/vm.html#drop-caches) | File data and metadata caches affect later I/O and CPU work. | A fresh process is not proof of a cold storage cache. Cache clearing can disrupt live work. |

The expected O(n + m) membership result follows from m average constant-time insertions and n average constant-time lookups, with bounded key costs. It includes index construction. The O(n × m) scan bound follows from examining up to m keys for each of n records. These are operation-growth analyses, not elapsed-time promises.

The user-supplied [public list-difference illustration](https://grok.com/share/c2hhcmQtNQ_b98a0c10-9399-4be4-9f04-aab8cc1cb482) was inaccessible during verification. It is not a technical authority for this package. Its code was not reviewed or executed. No private source material is distributed with the package.
