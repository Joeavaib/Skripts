"""Command-line evaluator for JSONL triage datasets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from metrics import EvalSample, json_validity_rate, macro_f1_score, policy_compliance_rate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run eval checks on a JSONL dataset.")
    parser.add_argument(
        "--dataset",
        default="packages/eval/data/sample_dataset.jsonl",
        help="Path to evaluation JSONL dataset.",
    )
    parser.add_argument(
        "--triage-f1-target",
        type=float,
        default=0.80,
        help="Minimum acceptable macro-F1 for triage predictions.",
    )
    return parser.parse_args()


def load_samples(dataset_path: Path) -> list[EvalSample]:
    samples: list[EvalSample] = []

    for line_number, raw_line in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue

        row = json.loads(raw_line)
        response_payload = row["response"]

        json_valid = True
        predicted_triage_label = ""
        try:
            parsed_response = json.loads(response_payload)
            predicted_triage_label = parsed_response["triage_label"]
        except (json.JSONDecodeError, KeyError, TypeError):
            json_valid = False

        sample = EvalSample(
            id=str(row.get("id", line_number)),
            json_valid=json_valid,
            policy_compliant=bool(row["policy_compliant"]),
            gold_triage_label=str(row["gold_triage_label"]),
            predicted_triage_label=str(predicted_triage_label),
        )
        samples.append(sample)

    if not samples:
        raise ValueError(f"Dataset has no samples: {dataset_path}")

    return samples


def main() -> int:
    args = parse_args()
    dataset_path = Path(args.dataset)
    samples = load_samples(dataset_path)

    json_rate = json_validity_rate(samples)
    policy_rate = policy_compliance_rate(samples)
    triage_f1 = macro_f1_score(samples)

    print(f"dataset={dataset_path}")
    print(f"samples={len(samples)}")
    print(f"json_validity_rate={json_rate:.4f}")
    print(f"policy_compliance_rate={policy_rate:.4f}")
    print(f"triage_macro_f1={triage_f1:.4f} target={args.triage_f1_target:.4f}")

    failed_checks: list[str] = []

    if json_rate < 1.0:
        failed_checks.append("JSON validity must be 100%.")
    if policy_rate < 1.0:
        failed_checks.append("Policy compliance must be 100%.")
    if triage_f1 < args.triage_f1_target:
        failed_checks.append("Triage macro-F1 below target.")

    if failed_checks:
        print("\nEVAL FAILED")
        for check in failed_checks:
            print(f"- {check}")
        return 1

    print("\nEVAL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
