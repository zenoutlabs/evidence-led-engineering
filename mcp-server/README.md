# Evidence-Led Engineering MCP

A small local [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server. An assistant that supports MCP can use it to review supplied timing measurements and read the engineering method.

Version 1.0 supports one tool and five guide resources. It uses standard input and output only. It does not start a web server, run benchmarks, execute supplied code, store experiment data, or connect to the ZenOut personal API.

## Get started

Install Python 3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Clone the repository:

```bash
git clone https://github.com/zenoutlabs/evidence-led-engineering.git
cd evidence-led-engineering
uv run --project mcp-server --frozen evidence-led-engineering-mcp --version
```

The command prints `1.0.0`. To start the MCP, omit `--version`. It then waits for protocol requests; it is not an interactive chat command. Stop a manual session with Control-C.

Configure an MCP-capable assistant to launch the server. A common JSON format is:

```json
{
  "mcpServers": {
    "evidence-led-engineering": {
      "command": "uv",
      "args": [
        "run", "--project", "/absolute/path/to/evidence-led-engineering/mcp-server",
        "--frozen", "evidence-led-engineering-mcp"
      ]
    }
  }
}
```

Replace the path with the actual checkout. Use the full path to `uv` if the assistant cannot find it. Client settings differ; this example describes the executable and arguments, not a tested configuration for every assistant. No global assistant settings are changed by this project.

After connection, ask: “Use `review_measurements` to compare these timings. Keep unknown experiment facts false.” Supply the measurements and evidence below. The assistant decides when to call its connected tools.

## Optional standalone installation

The server also builds into a wheel with its guide resources included. For an independent local command:

```bash
uv tool install --python 3.13 ./mcp-server
evidence-led-engineering-mcp --version
```

Use the installed command's full path in the client configuration. The package works outside the checkout; it does not read the original skill directory. This installation resolves transitive dependencies under the exact direct dependency pins. The source command with `--frozen` uses the complete checked-in dependency lock. The release check tests a clean wheel install with the locked dependency hashes.

To update the standalone command after reviewing a newer release, run the same install command with `--reinstall`. To remove it:

```bash
uv tool uninstall evidence-led-engineering-mcp
```

Remove the server entry from your assistant settings if you added one. Source-based users can remove that entry and their checkout instead.

## Tool and evidence

`review_measurements` accepts before-and-after elapsed-time samples from the same experiment:

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

This fictional example has medians of 11 ms and 5 ms. Its observed median speed ratio is 2.2. Function timings do not establish a whole-workflow improvement. The result is descriptive; it is not a statistical significance test or a promise of future performance.

Use 3..100 samples for each version, with equal counts. Each sample must be a finite number from 0.000001 to 86,400,000 milliseconds. Booleans, numeric strings, unknown arguments and unknown evidence fields are rejected. `scope` is `function` by default; use `workflow` only for the complete user-visible workflow.

The `evidence` object is required. Its six fields default to false. Set a field true only after checking it. `includes_setup` means both versions include setup required for the comparison being claimed. Compare cold and warm work separately.

The tool returns sample count, median, minimum, maximum, observed median speed ratio, elapsed-time reduction percentage, direction, range overlap, missing declared evidence, and cautions. Tool discovery publishes the complete input and output schemas. `schema_version` is 1; `independent_verification_performed` is always false.

The server accepts the caller's experiment facts. It does not verify outputs, source code, durability, provider behavior, clock accuracy, or operating conditions. A numeric result is not a correctness certificate.

## Guide resources

Read `evidence-led://guide/{section}` using one of these fixed sections:

| Section | Content |
| --- | --- |
| `method` | Concise skill |
| `measurement` | Experiment design |
| `semantics` | Behavior and safety contracts |
| `patterns` | Algorithms and data structures |
| `sources` | Primary technical source map |

Unknown sections and path traversal requests fail. These resources are bundled with the package. Their content is checked against the maintained skill. The server accepts no arbitrary file path or network destination. The host assistant's own logging and data-sharing policy still applies.

## Version 1 contract and support

Within version 1, the tool name, documented inputs and meanings, existing result fields, `schema_version=1`, and five resource addresses remain compatible. Breaking changes require a new major version. Additive behavior must remain compatible with existing callers. Guide wording and error messages can improve without a major release; do not parse error text. Invalid tool input returns an MCP tool error. Unknown resources return a protocol error. A valid request can follow an invalid one in the same session.

Verified environments are CPython 3.13 on macOS arm64 and Ubuntu 24.04 x64. The package metadata permits Python 3.10 and later where its dependencies support them; other Python versions and operating systems are not verified. Real SDK stdio sessions are tested. Specific coding-assistant products are not claimed as tested. Local v1 stability does not imply a hosted service or broad production adoption.

Report a reproducible problem through the repository's Issues page. Include the package version, Python version, OS, command, sanitized input, expected result and actual result. Do not include credentials, private records or assistant conversation logs. There is no paid support or response-time guarantee.

## Checks

```bash
uv run --project mcp-server --frozen python -m unittest discover -s mcp-server/tests -v
uv run --project mcp-server --frozen python mcp-server/check_install.py
python3 -m unittest discover -s tests -v
```

The installed-artifact check builds a wheel, verifies the MIT notice and five bundled resources, creates an isolated environment, installs hash-locked dependencies and the wheel, and starts the installed command from another folder. It checks discovery, output fields, invalid inputs, unknown tools, resource boundaries, recovery, and clean shutdown. The temporary environment is removed afterward.

See the [official MCP SDK guide](https://py.sdk.modelcontextprotocol.io/get-started/), [structured output](https://py.sdk.modelcontextprotocol.io/servers/structured-output/), and [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/).
