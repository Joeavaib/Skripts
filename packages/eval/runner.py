"""CLI eval runner with JSON, policy, and triage gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from packages.eval.metrics import compute_triage_metrics, find_policy_violations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run eval gates on a JSONL dataset.")
    parser.add_argument("--input", required=True, type=Path, help="Path to JSONL eval dataset")
    parser.add_argument(
        "--min-triage-score",
        type=float,
        default=0.7,
        help="Minimum acceptable triage_quality_score",
    )
    parser.add_argument(
        "--required",
        action="store_true",
        help="Fail the run if any gate fails; otherwise report only.",
    )
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    lines = args.input.read_text(encoding="utf-8").splitlines()

    valid_records: list[dict[str, object]] = []
    json_errors = 0
    policy_errors = 0

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            json_errors += 1
            print(f"[json-invalid] line {line_number}: {error.msg}")
            if args.required:
                return 1
            continue

        if not isinstance(record, dict):
            json_errors += 1
            print(f"[json-invalid] line {line_number}: top-level JSON must be an object")
            if args.required:
                return 1
            continue

        violations = find_policy_violations(record)
        if violations:
            policy_errors += 1
            print(f"[policy] line {line_number}: {'; '.join(violations)}")
            if args.required:
                return 1
            continue

        valid_records.append(record)

    metrics = compute_triage_metrics(valid_records)
    score = float(metrics["triage_quality_score"])
    print(
        "[summary] "
        f"records={len(valid_records)} json_errors={json_errors} "
        f"policy_errors={policy_errors} triage_quality_score={score:.3f}"
    )

    threshold_failed = score < args.min_triage_score
    if threshold_failed:
        print(
            f"[triage-metric] score {score:.3f} below threshold {args.min_triage_score:.3f}"
        )

    if args.required and (json_errors > 0 or policy_errors > 0 or threshold_failed):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
