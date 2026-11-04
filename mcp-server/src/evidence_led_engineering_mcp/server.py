"""Local MCP adapter for Evidence-Led Engineering. Launch with uv run server.py."""
import argparse
from importlib.resources import files
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .comparison import MAX_MS, MIN_MS, compare_timings


class EvidenceServer(MCPServer):
    """Keep the advertised and enforced v1 argument boundary identical."""

    async def list_tools(self):
        tools = await super().list_tools()
        for tool in tools:
            if tool.name == "review_measurements":
                tool.input_schema = {**tool.input_schema, "additionalProperties": False}
        return tools

    async def call_tool(self, name, arguments, context=None):
        if name == "review_measurements" and set(arguments) - {
            "baseline_ms", "candidate_ms", "evidence", "scope"
        }:
            raise ToolError("Unsupported argument. Use only baseline_ms, candidate_ms, evidence, and scope.")
        return await super().call_tool(name, arguments, context)


mcp = EvidenceServer(
    "Evidence-Led Engineering",
    version=__version__,
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


class SampleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    samples: int = Field(ge=3, le=100)
    median_ms: float = Field(ge=MIN_MS, le=MAX_MS, allow_inf_nan=False)
    minimum_ms: float = Field(ge=MIN_MS, le=MAX_MS, allow_inf_nan=False)
    maximum_ms: float = Field(ge=MIN_MS, le=MAX_MS, allow_inf_nan=False)


EvidenceField = Literal[
    "same_workload", "outputs_verified", "includes_setup",
    "same_environment", "uninstrumented", "operational_rules_preserved",
]


class TimingReview(BaseModel):
    """Version 1 result contract. Evidence remains caller-declared."""
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    scope: Literal["function", "workflow"]
    baseline: SampleSummary
    candidate: SampleSummary
    observed_median_speedup: float = Field(gt=0, allow_inf_nan=False)
    observed_elapsed_reduction_percent: float = Field(allow_inf_nan=False)
    candidate_elapsed_direction: Literal["lower", "higher", "equal"]
    ranges_overlap: bool
    missing_declared_evidence: list[EvidenceField]
    declared_evidence_complete: bool
    independent_verification_performed: Literal[False]
    cautions: list[str]


Milliseconds = Annotated[float, Field(strict=True, ge=MIN_MS, le=MAX_MS, allow_inf_nan=False)]
Samples = Annotated[list[Milliseconds], Field(min_length=3, max_length=100)]


@mcp.tool(structured_output=True, annotations=ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False,
))
def review_measurements(
    baseline_ms: Samples, candidate_ms: Samples, evidence: Evidence,
    scope: Literal["function", "workflow"] = "function",
) -> TimingReview:
    """Compare 3..100 elapsed-time samples per version, in milliseconds.

    Include index construction or other required setup in both one-shot samples.
    Declare experiment facts truthfully. False or omitted facts are reported as
    missing evidence. A result does not certify correctness or a production gain.
    """
    try:
        return TimingReview.model_validate(
            compare_timings(baseline_ms, candidate_ms, evidence.model_dump(), scope)
        )
    except ValueError as error:
        raise ToolError(str(error)) from error


GUIDE_ROOT = files("evidence_led_engineering_mcp").joinpath("guides")
SECTIONS = {
    "method": "method.md",
    "measurement": "measurement.md",
    "semantics": "semantic-contracts.md",
    "patterns": "optimization-patterns.md",
    "sources": "sources.md",
}


@mcp.resource("evidence-led://guide/{section}", mime_type="text/markdown")
def guide_section(section: str) -> str:
    """Read method, measurement, semantics, patterns, or sources from the bundle."""
    if section not in SECTIONS:
        raise ResourceNotFoundError("unknown guide section")
    return GUIDE_ROOT.joinpath(SECTIONS[section]).read_text(encoding="utf-8")


def main() -> None:
    """Run the local MCP over standard input and output."""
    parser = argparse.ArgumentParser(description="Evidence-Led Engineering local MCP server (stdio).")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
