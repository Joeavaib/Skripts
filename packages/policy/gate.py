from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import copy

DENY_ACTIONS = {"send", "delete"}
WRITE_SKILL_PREFIXES = ("write.", "skill.write.", "skills.write.")

# Only these deterministic.* keys may be overwritten by callers.
DETERMINISTIC_OVERWRITE_WHITELIST = {
    "deterministic.seed",
    "deterministic.trace_id",
    "deterministic.session_id",
}


@dataclass(frozen=True)
class GateResult:
    decision: str  # allow|confirm|deny
    risk_flags: tuple[str, ...]
    thread_pass: dict[str, Any]
    action_card: dict[str, Any]


class PolicyGate:
    """Evaluate hard-policy rules for action cards/thread passes."""

    def evaluate(
        self,
        thread_pass: Mapping[str, Any],
        action_card: Mapping[str, Any],
        deterministic_overwrites: Mapping[str, Any] | None = None,
    ) -> GateResult:
        tp = copy.deepcopy(dict(thread_pass))
        card = copy.deepcopy(dict(action_card))

        risk_flags: set[str] = set()
        decision = "allow"

        if not _has_why_1s(tp):
            risk_flags.add("missing_why_1s_thread_pass")
            decision = "deny"

        if not _has_why_1s(card):
            risk_flags.add("missing_why_1s_action_card")
            decision = "deny"

        action = str(card.get("action", "")).strip().lower()
        if action in DENY_ACTIONS:
            risk_flags.add(f"deny_action_{action}")
            decision = "deny"

        skill = str(card.get("skill", "")).strip().lower()
        if _is_write_skill(skill):
            risk_flags.add("confirm_required_write_skill")
            if decision != "deny":
                decision = "confirm"

        overwrite_flags = _apply_deterministic_overwrites(
            card,
            deterministic_overwrites or {},
            whitelist=DETERMINISTIC_OVERWRITE_WHITELIST,
        )
        risk_flags.update(overwrite_flags)

        # risk_flags are deterministic: policy-derived and sorted; caller input never wins.
        card["risk_flags"] = sorted(risk_flags)

        return GateResult(
            decision=decision,
            risk_flags=tuple(sorted(risk_flags)),
            thread_pass=tp,
            action_card=card,
        )


def _is_write_skill(skill: str) -> bool:
    return any(skill.startswith(prefix) for prefix in WRITE_SKILL_PREFIXES) or skill == "write"


def _has_why_1s(payload: Mapping[str, Any]) -> bool:
    why_1s = payload.get("why_1s")
    if not isinstance(why_1s, str):
        return False

    text = why_1s.strip()
    if not text:
        return False

    # Enforce one short sentence.
    sentence_terminators = sum(text.count(x) for x in (".", "!", "?"))
    if sentence_terminators > 1:
        return False

    if "\n" in text:
        return False

    return True


def _apply_deterministic_overwrites(
    action_card: dict[str, Any],
    overwrites: Mapping[str, Any],
    whitelist: set[str],
) -> set[str]:
    flags: set[str] = set()
    if not overwrites:
        return flags

    deterministic = action_card.setdefault("deterministic", {})
    if not isinstance(deterministic, dict):
        deterministic = {}
        action_card["deterministic"] = deterministic

    for key, value in sorted(overwrites.items()):
        if not key.startswith("deterministic."):
            continue

        if key not in whitelist:
            flags.add("deterministic_overwrite_blocked")
            continue

        _, subkey = key.split(".", 1)
        deterministic[subkey] = value
        flags.add("deterministic_overwrite_applied")

    return flags
