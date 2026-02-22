"""Metrics and policy checks for eval datasets."""

from __future__ import annotations

from collections.abc import Iterable

ALLOWED_TRIAGE_LABELS = {"accept", "review", "reject"}
REQUIRED_FIELDS = {"id", "prompt", "response", "policy_tags", "triage_label"}
BANNED_RESPONSE_SUBSTRINGS = {"password", "secret key", "api key"}


def find_policy_violations(record: dict[str, object]) -> list[str]:
    """Return a list of policy violations for a record."""
    violations: list[str] = []

    missing = REQUIRED_FIELDS - set(record.keys())
    if missing:
        violations.append(f"missing required fields: {sorted(missing)}")
        return violations

    policy_tags = record.get("policy_tags")
    if not isinstance(policy_tags, list) or not all(isinstance(tag, str) for tag in policy_tags):
        violations.append("policy_tags must be a list of strings")

    triage_label = record.get("triage_label")
    if triage_label not in ALLOWED_TRIAGE_LABELS:
        violations.append(f"triage_label must be one of {sorted(ALLOWED_TRIAGE_LABELS)}")

    for text_field in ("prompt", "response"):
        value = record.get(text_field)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"{text_field} must be a non-empty string")

    response = str(record.get("response", "")).lower()
    for banned in BANNED_RESPONSE_SUBSTRINGS:
        if banned in response:
            violations.append(f"response contains banned substring: {banned}")

    return violations


def is_policy_compliant(record: dict[str, object]) -> bool:
    """Check whether a record is policy compliant."""
    return not find_policy_violations(record)


def compute_triage_metrics(records: Iterable[dict[str, object]]) -> dict[str, float | int]:
    """Compute a base triage metric from labels.

    triage_quality_score weights labels as:
      - accept: 1.0
      - review: 0.5
      - reject: 0.0
    """
    weights = {"accept": 1.0, "review": 0.5, "reject": 0.0}
    accepted = reviewed = rejected = 0
    total = 0
    score_sum = 0.0

    for record in records:
        label_obj = record.get("triage_label")
        if not isinstance(label_obj, str) or label_obj not in ALLOWED_TRIAGE_LABELS:
            continue
        label = label_obj
        total += 1
        score_sum += weights[label]
        if label == "accept":
            accepted += 1
        elif label == "review":
            reviewed += 1
        else:
            rejected += 1

    triage_quality_score = score_sum / total if total else 0.0
    return {
        "total_labeled": total,
        "accepted": accepted,
        "reviewed": reviewed,
        "rejected": rejected,
        "triage_quality_score": triage_quality_score,
    }
