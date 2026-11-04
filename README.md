# Evidence-Led Engineering

**Help your coding agent measure performance, improve the right code, and preserve correct behavior.**

A portable coding-agent skill, practical guide, and optional local MCP server from [ZenOut Labs](https://zenoutlabs.com/).

Start with the measured workflow. Choose a suitable algorithm or data structure. Make a small change. Check the result before claiming an improvement. Apply the method across languages and projects. Scale the work to the task: a small edit does not need a full performance audit.

## Try it

```bash
git clone https://github.com/zenoutlabs/evidence-led-engineering.git
cd evidence-led-engineering
python3 -m unittest discover -s tests -v
python3 skills/evidence-led-performance/scripts/performance_examples.py
```

The core examples use Python 3.9 or later and the standard library. They use fictional data. See [validation and limits](docs/VALIDATION.md) for the tested environments.

## Choose your entry point

| Use | Start here |
| --- | --- |
| Learn the method | [Practical guide](GUIDE.md) |
| Guide a coding agent | [Portable skill](skills/evidence-led-performance/SKILL.md) |
| Review supplied timings through MCP | [Optional MCP setup](mcp-server/README.md) |
| Check technical claims | [Primary sources](skills/evidence-led-performance/references/sources.md) |

For Codex, copy the complete `skills/evidence-led-performance` folder into the skill location used by your installation, or provide its local `SKILL.md` path. Keep its references, scripts, and license together. Other coding agents can use the same Markdown guidance. Client installation formats can differ.

```text
Use $evidence-led-performance for this task.
Find the measured cause of the slow workflow.
Preserve its outputs, scope, owner decisions, and operational limits.
Make the smallest justified change and show the checks and measurements.
```

## What the method protects

- Scope, duplicates, output order, and exact arithmetic.
- Owner decisions, cache invalidation, durability, and provider rules.
- Comparable workloads, including index construction and realistic hit rates.
- Clear separation of computation, I/O, network, pacing, waits, and UI delay.

Use profilers to locate work. Use separate repeated timings to establish speed. Consider a native component only for a remaining measured bottleneck with a stable contract and justified integration cost.

## Run the bounded benchmark

```bash
python3 skills/evidence-led-performance/scripts/benchmark_membership.py --help
python3 skills/evidence-led-performance/scripts/benchmark_membership.py
```

It compares a repeated membership scan with a scoped hash index. It preserves left order and duplicates. Its JSON includes fixture parameters and digest, raw repetitions, index construction, reuse, operation counts, and separate traced Python allocation peaks. It enforces workload limits. No timing threshold determines test success.

These are illustrative measurements. They do not predict a speedup for another application. An index can cost more than a short scan when lookups match early.

## Optional local MCP — experimental

MCP means Model Context Protocol. Compatible AI applications can call `review_measurements` and read five fixed guide sections. The tool compares supplied timing samples and reports missing experiment facts. Those facts remain caller declarations, rather than independent proof.

```bash
uv run --project mcp-server --frozen python mcp-server/server.py
```

This component requires Python 3.10 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/). It uses the locked official MCP SDK. It waits for a client on standard input and output. Read the [setup guide](mcp-server/README.md) for a client configuration and sample request.

It accepts bounded measurements rather than arbitrary commands or file paths. It has no hosted endpoint, account service, or billing system in this release.

## Development

```bash
python3 -m unittest discover -s tests -v
uv run --project mcp-server --frozen python -m unittest discover -s mcp-server/tests -v
```

For a change, include the user problem, behavior checks, and measurement conditions when performance is claimed. Keep example data fictional. Report regressions and resource costs alongside favorable results. Use topic branches and pull requests.

## License

[MIT](LICENSE). Copyright 2026 ZenOut Labs. The portable skill includes a copy of the license so it can travel with its files. Dependencies retain their own licenses.
