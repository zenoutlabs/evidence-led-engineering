"""Bounded descriptive timing comparisons. No I/O and no code execution."""
from __future__ import annotations

import math
import statistics


EVIDENCE_FIELDS = (
    "same_workload", "outputs_verified", "includes_setup",
    "same_environment", "uninstrumented", "operational_rules_preserved",
)
MIN_MS = 0.000001
MAX_MS = 86_400_000
MAX_SAMPLES = 100


def _samples(values: list[float], name: str) -> list[float]:
    if type(values) is not list or not 3 <= len(values) <= MAX_SAMPLES:
        raise ValueError(f"{name} must contain 3..100 samples")
    if any(type(v) not in (int, float) or not MIN_MS <= v <= MAX_MS
           or not math.isfinite(v) for v in values):
        raise ValueError(f"{name} samples must be finite milliseconds from {MIN_MS} to {MAX_MS}")
    return [float(v) for v in values]


def compare_timings(
    baseline_ms: list[float], candidate_ms: list[float],
    evidence: dict[str, bool], scope: str = "function",
) -> dict:
    """Summarize supplied samples. Caller declarations are not independent proof."""
    baseline = _samples(baseline_ms, "baseline_ms")
    candidate = _samples(candidate_ms, "candidate_ms")
    if len(baseline) != len(candidate):
        raise ValueError("use the same sample count for this comparison")
    if scope not in ("function", "workflow"):
        raise ValueError("scope must be function or workflow")
    if type(evidence) is not dict or set(evidence) != set(EVIDENCE_FIELDS):
        raise ValueError("supply exactly the six documented evidence fields")
    if any(type(v) is not bool for v in evidence.values()):
        raise ValueError("evidence fields must be booleans")

    def summarize(values):
        return {"samples": len(values), "median_ms": statistics.median(values),
                "minimum_ms": min(values), "maximum_ms": max(values)}

    before, after = summarize(baseline), summarize(candidate)
    ratio = before["median_ms"] / after["median_ms"]
    direction = "lower" if ratio > 1 else "higher" if ratio < 1 else "equal"
    missing = [field for field in EVIDENCE_FIELDS if not evidence[field]]
    overlap = max(min(baseline), min(candidate)) <= min(max(baseline), max(candidate))
    cautions = [
        "Experiment facts are declared by the caller. This tool does not verify outputs or run the workload.",
        "This is a descriptive comparison. It does not establish statistical significance or future performance.",
    ]
    if missing:
        cautions.append("Resolve missing experiment evidence before using these timings to justify a change.")
    if overlap:
        cautions.append("Observed ranges overlap. Inspect noise, trial order, and the raw samples.")
    if direction == "higher":
        cautions.append("The candidate median is slower for these supplied samples.")
    if scope == "function":
        cautions.append("Function timings do not establish a whole-workflow improvement.")
    return {
        "schema_version": 1, "scope": scope,
        "baseline": before, "candidate": after,
        "observed_median_speedup": ratio,
        "observed_elapsed_reduction_percent": (1 - after["median_ms"] / before["median_ms"]) * 100,
        "candidate_elapsed_direction": direction,
        "ranges_overlap": overlap,
        "missing_declared_evidence": missing,
        "declared_evidence_complete": not missing,
        "independent_verification_performed": False,
        "cautions": cautions,
    }
