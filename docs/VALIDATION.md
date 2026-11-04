# Validation and limits

The core suite has 25 deterministic tests. It covers scoped membership, left order and duplicates, index rebuilds, cache dependencies and owner decisions, exact integer money, and batch caps and cancellation.

The optional MCP suite has 9 tests. It checks the timing arithmetic, invalid inputs, missing experiment facts, resource boundaries, and an actual standard-input/output client session. It asserts structured numeric output, rather than only a successful connection.

Local checks on November 4, 2026 passed on CPython 3.9.6 for the core and CPython 3.13.14 for the MCP on macOS arm64. The MCP used the locked SDK 2.3.0 and Pydantic 2.14.2. CI records any further environment checks.

The included benchmark uses fictional in-memory inputs. Its outputs are checked against the reference scan. One-shot results include index construction. Timings and traced Python allocations are collected in separate runs. Work has an enforced operation bound. Timing does not determine test success.

The MCP reviews supplied measurements. Its experiment facts are caller declarations. It does not execute code, verify outputs, establish statistical significance, or certify a production gain. It has no public hosted endpoint in this release.

No real database, network, provider, durable-write, crash-recovery, concurrent-mutation, or UI integration is tested by these examples. A real project needs its own representative workflow and safety checks.

The first local MCP protocol test found missing structured output. The final adapter declares an explicit dictionary type and requires structured output. Expected resource and tool failures use SDK error classes. The final protocol tests cover these behaviors.
