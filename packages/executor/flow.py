from __future__ import annotations

from dataclasses import dataclass

from packages.llm.writer import Writer, WriterInput


@dataclass
class Message:
    body: str


class ExecutorFlow:
    """Executor orchestration that drafts and patches a reply message."""

    def __init__(self, writer: Writer) -> None:
        self._writer = writer

    def patch_message(self, message: Message, patch_text: str) -> Message:
        message.body = patch_text
        return message

    def run(self, *, message: Message, redacted_excerpt: str, facts: list[str]) -> Message:
        draft = self._writer.create_reply_draft(
            WriterInput(redacted_excerpt=redacted_excerpt, facts=facts)
        )
        return self.patch_message(message, draft)
