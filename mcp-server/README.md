# Evidence-Led Engineering MCP

An optional local Model Context Protocol (MCP) server. It lets an AI coding assistant compare supplied timing evidence and read the method. The original skill and examples work without this component.

## Useful task

Give `review_measurements` before-and-after elapsed-time samples from the same experiment. It returns median, minimum, maximum, an observed speed ratio, and missing evidence. It reports regressions and overlapping ranges. It performs no statistical significance test.

The experiment facts are declarations from the caller. The server does not verify source code, outputs, durability, or provider behavior. A numeric result is not a correctness certificate or a prediction of production performance.

## Run locally

Use Python 3.10 or later and `uv`. This component was tested on CPython 3.13.14 with the official MCP SDK 2.3.0 on macOS arm64. The lock file fixes its dependency versions. Other environments are untested.

From the repository folder:

```bash
uv run --project mcp-server --frozen python mcp-server/server.py
```

The process uses standard input and output for protocol messages. A terminal with no MCP client will wait for requests. Stop it with Control-C. No HTTP endpoint is started.

Example assistant configuration:

```json
{
  "mcpServers": {
    "evidence-led-engineering": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/evidence-led-engineering/mcp-server",
        "run", "--frozen", "server.py"
      ]
    }
  }
}
```

Replace the example path with the actual folder. Client settings formats differ. Supply the same command and arguments in your client's format. No settings are installed by this package. A real SDK client session was tested; specific coding-agent applications were not tested.

## Tool input

```json
{
  "baseline_ms": [12, 10, 11],
  "candidate_ms": [4, 5, 6],
  "scope": "function",
  "evidence": {
    "same_workload": true,
    "outputs_verified": true,
    "includes_setup": true,
    "same_environment": true,
    "uninstrumented": true,
    "operational_rules_preserved": true
  }
}
```

This fictional example has medians of 11 ms and 5 ms. Its observed median speed ratio is 2.2. Its scope is one function, so it does not establish a workflow improvement.

Use 3..100 samples for each implementation, with equal sample counts. Values must be finite milliseconds between 0.000001 and 86,400,000. These bounds keep calculations small and reject zero-resolution and excessive values. They do not establish clock accuracy. Unknown evidence fields, booleans used as times, invalid scopes, and non-finite values are rejected.

Each evidence flag defaults to false. Supply true only when the corresponding experiment condition was checked. `includes_setup` means both versions include the setup required for the comparison being claimed. If the experiment excludes a required index build, report false. Compare cold and warm work separately.

`scope` is `function` by default. Use `workflow` only for samples measured across the complete user-visible workflow.

## Method resources

The resource template is `evidence-led://guide/{section}`. It accepts five fixed sections:

- `method`: the concise skill.
- `measurement`: experiment design and interpretation.
- `semantics`: behavior and safety contracts.
- `patterns`: algorithm and data-structure choices.
- `sources`: the primary technical source map.

Other section names are rejected. The server accepts no shell commands, arbitrary file paths, or network destinations. It does not execute benchmarks, persist experiment data, or connect to a personal-data API. A local MCP host and its own logging policy still determine where its conversation data is stored.

## Checks

```bash
uv run --project mcp-server --frozen python -m unittest discover -s mcp-server/tests -v
```

The suite checks calculation results, regressions, missing facts, strict boundaries, actual stdio discovery and calls, structured output, and resource access. The original suite remains separate:

```bash
python3 -m unittest discover -s tests -v
```

See the [official SDK guide](https://py.sdk.modelcontextprotocol.io/get-started/), [structured output](https://py.sdk.modelcontextprotocol.io/servers/structured-output/), and [error handling](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/). A hosted MCP would be a separate deployment decision after local usage shows a need.
