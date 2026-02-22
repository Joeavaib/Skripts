"""Evaluation metric helpers for structured assistant responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EvalSample:
    """Single sample used for evaluation."""

    id: str
    json_valid: bool
    policy_compliant: bool
    gold_triage_label: str
    predicted_triage_label: str


def json_validity_rate(samples: Iterable[EvalSample]) -> float:
    """Return the share of samples whose response JSON is valid."""
    sample_list = list(samples)
    if not sample_list:
        return 0.0
    return sum(1 for sample in sample_list if sample.json_valid) / len(sample_list)


def policy_compliance_rate(samples: Iterable[EvalSample]) -> float:
    """Return the share of samples that satisfy policy checks."""
    sample_list = list(samples)
    if not sample_list:
        return 0.0
    return sum(1 for sample in sample_list if sample.policy_compliant) / len(sample_list)


def macro_f1_score(samples: Iterable[EvalSample]) -> float:
    """Compute unweighted macro-F1 for triage labels."""
    sample_list = list(samples)
    if not sample_list:
        return 0.0

    labels = sorted(
        {sample.gold_triage_label for sample in sample_list}
        | {sample.predicted_triage_label for sample in sample_list}
    )
    f1_scores: list[float] = []

    for label in labels:
        tp = sum(
            1
            for sample in sample_list
            if sample.gold_triage_label == label and sample.predicted_triage_label == label
        )
        fp = sum(
            1
            for sample in sample_list
            if sample.gold_triage_label != label and sample.predicted_triage_label == label
        )
        fn = sum(
            1
            for sample in sample_list
            if sample.gold_triage_label == label and sample.predicted_triage_label != label
        )

        precision = tp / (tp + fp) if tp + fp > 0 else 0.0
        recall = tp / (tp + fn) if tp + fn > 0 else 0.0

        if precision + recall == 0:
            f1_scores.append(0.0)
        else:
            f1_scores.append(2 * precision * recall / (precision + recall))

    return sum(f1_scores) / len(f1_scores)
