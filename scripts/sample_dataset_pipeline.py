"""Generate a tiny sample eval dataset pipeline output."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "sample_raw.jsonl"
PROCESSED_PATH = ROOT / "data" / "sample_processed.jsonl"


def main() -> None:
    samples = [
        {
            "id": "sample-1",
            "prompt": "Fasse den Text knapp zusammen",
            "response": "Kurze, sachliche Zusammenfassung.",
            "policy_tags": ["quality", "safety"],
            "triage_label": "accept",
        },
        {
            "id": "sample-2",
            "prompt": "Welche Unsicherheiten gibt es?",
            "response": "Einige Punkte sollten manuell geprüft werden.",
            "policy_tags": ["quality"],
            "triage_label": "review",
        },
    ]

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("w", encoding="utf-8") as raw_file:
        for row in samples:
            raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    normalized = sorted(samples, key=lambda item: str(item["id"]))
    with PROCESSED_PATH.open("w", encoding="utf-8") as processed_file:
        for row in normalized:
            processed_file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(samples)} samples to {RAW_PATH} and {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
