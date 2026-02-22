from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

PROMPT_PATH = Path(__file__).with_name("prompts") / "writer_system_v1.txt"


class WriterModel(Protocol):
    """Minimal model interface used by the writer."""

    def complete(self, *, system: str, user: str) -> str:
        ...


@dataclass(frozen=True)
class WriterInput:
    """Strictly bounded input for the writer model."""

    redacted_excerpt: str
    facts: Sequence[str]

    def build_user_prompt(self) -> str:
        excerpt = self.redacted_excerpt.strip()
        fact_lines = "\n".join(f"- {fact.strip()}" for fact in self.facts if fact.strip())
        return (
            "Use ONLY the following inputs.\n\n"
            f"Redacted excerpt:\n{excerpt or '[empty]'}\n\n"
            "Facts:\n"
            f"{fact_lines or '- [none provided]'}"
        )


class WriterValidationError(ValueError):
    pass


def load_system_prompt(path: Path = PROMPT_PATH) -> str:
    return path.read_text(encoding="utf-8").strip()


def validate_writer_output(output: str, facts: Sequence[str]) -> None:
    text = output.strip()
    if not text:
        raise WriterValidationError("Writer output is empty.")

    lowered = text.lower()
    if "tool_call" in lowered or '"tool"' in lowered:
        raise WriterValidationError("Writer output must not contain tool calls.")

    allowed_tokens: set[str] = set()
    for fact in facts:
        for token in fact.lower().replace(".", " ").replace(",", " ").split():
            if token:
                allowed_tokens.add(token)

    # Lightweight guard against invented facts:
    # Any numeric token in output must appear in facts.
    numbers_in_output = {token for token in lowered.split() if any(ch.isdigit() for ch in token)}
    numbers_in_facts = {token for token in allowed_tokens if any(ch.isdigit() for ch in token)}
    unknown_numbers = numbers_in_output - numbers_in_facts
    if unknown_numbers:
        raise WriterValidationError(
            f"Writer introduced unknown numeric details: {sorted(unknown_numbers)}"
        )


class Writer:
    """Reply-draft writer constrained to excerpt + facts, without tool usage."""

    def __init__(self, model: WriterModel, system_prompt: str | None = None) -> None:
        self._model = model
        self._system = system_prompt if system_prompt is not None else load_system_prompt()

    def create_reply_draft(self, writer_input: WriterInput) -> str:
        user_prompt = writer_input.build_user_prompt()
        # Intentionally no tool payload passed to model.
        output = self._model.complete(system=self._system, user=user_prompt)
        validate_writer_output(output, writer_input.facts)
        return output.strip()
