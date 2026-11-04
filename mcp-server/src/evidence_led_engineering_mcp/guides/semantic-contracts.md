# Preserve behavior and safety

Read this before optimizing stateful work, money calculations, scoped data, caches, writes, or provider calls. Select checks based on what the proposed change can affect.

## Write the contract first

| Invariant | A useful check |
| --- | --- |
| Scope | Equal record IDs in two owners or tenants do not cross-match |
| Duplicates | Repeated left records remain repeated if the contract requires this |
| Ordering | Output order matches the specified order, including ties |
| Key semantics | Case, nulls, normalization, and composite keys behave as specified |
| Money | Integer minor units or suitable decimal arithmetic preserve currency and rounding rules |
| Owner decisions | An override changes the result and invalidates any dependent cache |
| Cache validity | Data, rules, scope, and decision versions cannot return an old result |
| Durability | A success response still means the required state survives the specified failure |
| Side effects | Retries, batches, and cancellation do not create duplicate or lost effects |
| Provider safety | Request size, rate, concurrency, quota, and backoff constraints remain in force |

Use exact arithmetic appropriate to the domain. Integer minor units are useful for currencies with a defined minor-unit scale. They do not remove the need to define currency, conversion, tax, and rounding rules. Validate overflow in fixed-width native code. Do not silently replace decimal calculations with binary floating point.

## Differential checks

Run the reference and candidate on the same inputs. Compare observable outputs and relevant effects. Check empty, one-item, no-match, all-match, repeated, out-of-order, and mixed-scope inputs. Add deterministic randomized cases with a fixed seed when they cover combinations economically.

Output equality alone may miss lost writes, extra requests, changed authorization, or delayed visibility. Compare those effects when they are part of the contract. Use an independent expected result for known bugs. Do not require parity with incorrect behavior.

Keep diagnostic counters outside timed functions. Tests should catch changed behavior, not just repeat implementation details or assert that one version is faster on a busy machine.

## Cache contracts

Define the identity of a computation. Include all data that can change its answer: tenant or owner scope, immutable data version, rules version, owner decision version, and other effective inputs. A version label is useful only if the writer advances it on every relevant mutation.

Keep a clear path for invalidation, eviction, and miss handling. Test cached negative results as well as successful results. Bound memory. Avoid returning mutable shared objects that callers can change. State the concurrency model. A single-thread example does not prove safe publication or invalidation under concurrent writers.

For persistent caches, also define compatibility across deployments and recovery after partial writes. Cache keys alone do not provide transactional consistency between independently updated inputs.

## Writes, retries, and cancellation

Batching can change failure behavior. Record what happens when item k fails, when a process exits, and when a provider times out after accepting a request. Use the project's transaction or idempotency mechanism. Preserve commit and flush requirements. A faster test with weaker synchronization is a different durability contract.

Test cancellation at a useful boundary. State which work may already have completed. Do not claim that cancellation reverses effects already accepted by a provider.

Separate provider batch-size caps from rate limits and concurrency limits. A legal batch size does not establish a safe request rate. Never raise a limit, skip backoff, or weaken a rule to make a benchmark pass.

## Rollout evidence

Use a small reversible change when practical. Retain the baseline, compare real workflow outcomes, and use the project's normal rollback path. For high-impact changes, exercise error recovery and crash behavior in a safe test environment. The bundled examples test in-memory semantics only. They do not prove production durability, concurrency, authorization, or provider safety.
