from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_runner_required_passes(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        '{"id":"1","prompt":"a","response":"b","policy_tags":["x"],"triage_label":"accept"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "packages.eval.runner",
            "--input",
            str(dataset),
            "--required",
            "--min-triage-score",
            "0.7",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
