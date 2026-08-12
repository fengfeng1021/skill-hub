#!/usr/bin/env python3
"""Compare matched control/skill benchmark result JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


LOWER_IS_BETTER = {"criticalRegressions", "durationSeconds", "tokens"}
QUALITY_METRICS = {
    "requirementsPassRate",
    "automatedPassRate",
    "designQuality",
    "codeQuality",
    "accessibilityScore",
    "performanceScore",
    "securityScore",
    "criticalRegressions",
}


def load_results(paths: list[str]) -> list[dict[str, Any]]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)
    results: list[dict[str, Any]] = []
    for path in files:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc
        required = {"schemaVersion", "runId", "variant", "agent", "model", "taskId", "seed", "metrics"}
        missing = required - set(item)
        if missing:
            raise ValueError(f"{path} is missing: {', '.join(sorted(missing))}")
        if item["variant"] not in {"control", "skill", "ablation"}:
            raise ValueError(f"{path} has an invalid variant")
        for name, value in item["metrics"].items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{path}: metric {name} must be numeric")
            if name in QUALITY_METRICS - {"criticalRegressions"} and not 0 <= value <= 100:
                raise ValueError(f"{path}: metric {name} must be between 0 and 100")
        results.append(item)
    return results


def key(item: dict[str, Any]) -> tuple[str, str, str, str]:
    return item["agent"], item["model"], item["taskId"], str(item["seed"])


def compare(results: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for item in results:
        variant = item["variant"]
        if variant in grouped[key(item)]:
            raise ValueError(f"Duplicate {variant} result for {key(item)}")
        grouped[key(item)][variant] = item

    pairs: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for pair_key, variants in sorted(grouped.items()):
        if "control" not in variants or "skill" not in variants:
            unmatched.append({"key": pair_key, "variants": sorted(variants)})
            continue
        control = variants["control"]["metrics"]
        skill = variants["skill"]["metrics"]
        metric_names = sorted(set(control).intersection(skill))
        deltas = {
            name: (control[name] - skill[name] if name in LOWER_IS_BETTER else skill[name] - control[name])
            for name in metric_names
        }
        quality_deltas = [value for name, value in deltas.items() if name in QUALITY_METRICS]
        pairs.append(
            {
                "agent": pair_key[0],
                "model": pair_key[1],
                "taskId": pair_key[2],
                "seed": pair_key[3],
                "deltas": deltas,
                "qualityDeltaMean": mean(quality_deltas) if quality_deltas else None,
            }
        )

    metric_values: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        for name, value in pair["deltas"].items():
            metric_values[name].append(value)
    aggregate = {name: mean(values) for name, values in sorted(metric_values.items())}
    regressions = [
        {"agent": pair["agent"], "model": pair["model"], "taskId": pair["taskId"], "metric": name, "delta": value}
        for pair in pairs
        for name, value in pair["deltas"].items()
        if name in QUALITY_METRICS and value < 0
    ]
    return {
        "matchedPairs": len(pairs),
        "unmatched": unmatched,
        "aggregateDeltas": aggregate,
        "qualityRegressions": regressions,
        "pairs": pairs,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = ["# Frontend Director A/B Report", "", f"Matched pairs: {report['matchedPairs']}", ""]
    if not report["matchedPairs"]:
        lines.append("No matched control/skill pairs; no quality claim can be made.")
        return "\n".join(lines)
    lines.extend(["| Metric | Mean improvement |", "|---|---:|"])
    for name, value in report["aggregateDeltas"].items():
        lines.append(f"| {name} | {value:+.2f} |")
    lines.extend(["", f"Quality regressions: {len(report['qualityRegressions'])}"])
    if report["unmatched"]:
        lines.append(f"Unmatched runs: {len(report['unmatched'])}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Result JSON files or directories")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    try:
        report = compare(load_results(args.paths))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else markdown(report))
    return 0 if report["matchedPairs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
