"""Local MCP adapter for Evidence-Led Engineering. Launch with uv run server.py."""
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from comparison import MAX_MS, MIN_MS, compare_timings


mcp = MCPServer(
    "Evidence-Led Engineering",
    version="0.2.0",
    instructions="Compare supplied timing evidence and read the performance method. "
                 "Treat experiment facts as caller declarations. Preserve scope and operational rules.",
)


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    same_workload: bool = False
    outputs_verified: bool = False
    includes_setup: bool = False
    same_environment: bool = False
    uninstrumented: bool = False
    operational_rules_preserved: bool = False


Milliseconds = Annotated[float, Field(strict=True, ge=MIN_MS, le=MAX_MS, allow_inf_nan=False)]
Samples = Annotated[list[Milliseconds], Field(min_length=3, max_length=100)]


@mcp.tool(structured_output=True, annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False,
))
def review_measurements(
    baseline_ms: Samples, candidate_ms: Samples, evidence: Evidence,
    scope: Literal["function", "workflow"] = "function",
) -> dict[str, Any]:
    """Compare 3..100 elapsed-time samples per version, in milliseconds.

    Include index construction or other required setup in both one-shot samples.
    Declare experiment facts truthfully. False or omitted facts are reported as
    missing evidence. A result does not certify correctness or a production gain.
    """
    try:
        return compare_timings(baseline_ms, candidate_ms, evidence.model_dump(), scope)
    except ValueError as error:
        raise ToolError(str(error)) from error


GUIDE_ROOT = Path(__file__).resolve().parents[1] / "skills/evidence-led-performance"
SECTIONS = {
    "method": "SKILL.md",
    "measurement": "references/measurement.md",
    "semantics": "references/semantic-contracts.md",
    "patterns": "references/optimization-patterns.md",
    "sources": "references/sources.md",
}


@mcp.resource("evidence-led://guide/{section}", mime_type="text/markdown")
def guide_section(section: str) -> str:
    """Read method, measurement, semantics, patterns, or sources from the bundle."""
    if section not in SECTIONS:
        raise ResourceNotFoundError("unknown guide section")
    return (GUIDE_ROOT / SECTIONS[section]).read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run(transport="stdio")
