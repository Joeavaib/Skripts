"""Policy gate for action execution decisions."""

from __future__ import annotations

from dataclasses import dataclass


DENY_ACTIONS = {"send", "delete"}
WRITE_SKILLS = {"move", "categories", "flag", "send", "delete"}


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    reason: str


def evaluate_action_gate(action: str, *, confirm: bool = False) -> GateDecision:
    """Evaluate whether an action is allowed.

    Rules:
    - ``send`` and ``delete`` are always denied.
    - write skills require explicit ``confirm=True``.
    """

    normalized = action.strip().lower()

    if normalized in DENY_ACTIONS:
        return GateDecision(allowed=False, reason="action_denied")

    if normalized in WRITE_SKILLS and not confirm:
        return GateDecision(allowed=False, reason="confirm_required")

    return GateDecision(allowed=True, reason="allowed")
