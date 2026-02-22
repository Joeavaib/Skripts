from __future__ import annotations

import pytest

from packages.executor.flow import ExecutorFlow, Message
from packages.llm.writer import Writer, WriterInput, WriterValidationError, validate_writer_output


class StubModel:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        return self.response


def test_writer_uses_only_excerpt_and_facts_prompt_shape() -> None:
    model = StubModel("Antwort mit Fakt 42")
    writer = Writer(model=model, system_prompt="sys")

    writer.create_reply_draft(WriterInput(redacted_excerpt="Ticket [REDACTED]", facts=["ID 42"]))

    call = model.calls[0]
    assert call["system"] == "sys"
    assert "Redacted excerpt" in call["user"]
    assert "Facts" in call["user"]
    assert "Ticket [REDACTED]" in call["user"]


def test_no_invented_facts_rule_rejects_unknown_numbers_from_stubbed_writer_output() -> None:
    with pytest.raises(WriterValidationError):
        validate_writer_output("Ihr Vorgang ist 99 Tage alt.", ["Vorgang ist 42 Tage alt"])


def test_executor_flow_integrates_create_reply_draft_and_patch_message() -> None:
    model = StubModel("Finale Antwort basierend auf Fakt 123")
    writer = Writer(model=model, system_prompt="sys")
    flow = ExecutorFlow(writer)
    message = Message(body="old")

    updated = flow.run(
        message=message,
        redacted_excerpt="Kunde fragt nach Status",
        facts=["Ticketnummer 123"],
    )

    assert updated.body == "Finale Antwort basierend auf Fakt 123"


def test_writer_rejects_tool_calls() -> None:
    with pytest.raises(WriterValidationError):
        validate_writer_output('{"tool_call": "search"}', ["irrelevant"])
