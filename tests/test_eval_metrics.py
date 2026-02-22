from packages.eval.metrics import compute_triage_metrics, find_policy_violations


def test_find_policy_violations_missing_fields() -> None:
    violations = find_policy_violations({"id": "x"})
    assert violations


def test_compute_triage_metrics() -> None:
    metrics = compute_triage_metrics(
        [
            {"triage_label": "accept"},
            {"triage_label": "review"},
            {"triage_label": "reject"},
        ]
    )
    assert metrics["total_labeled"] == 3
    assert metrics["triage_quality_score"] == 0.5
