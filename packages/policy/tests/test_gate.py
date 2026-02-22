import copy

from packages.policy.gate import PolicyGate


def _valid_thread_pass():
    return {"thread_id": "t-1", "why_1s": "Need a safe policy decision."}


def _valid_action_card():
    return {
        "action": "read",
        "skill": "tool.read.file",
        "why_1s": "Reading config for context.",
        "risk_flags": ["caller_supplied"],
    }


def test_deny_send_action():
    gate = PolicyGate()
    card = _valid_action_card()
    card["action"] = "send"

    result = gate.evaluate(_valid_thread_pass(), card)

    assert result.decision == "deny"
    assert "deny_action_send" in result.risk_flags


def test_deny_delete_action():
    gate = PolicyGate()
    card = _valid_action_card()
    card["action"] = "delete"

    result = gate.evaluate(_valid_thread_pass(), card)

    assert result.decision == "deny"
    assert "deny_action_delete" in result.risk_flags


def test_confirm_required_for_write_skill():
    gate = PolicyGate()
    card = _valid_action_card()
    card["skill"] = "write.db.record"

    result = gate.evaluate(_valid_thread_pass(), card)

    assert result.decision == "confirm"
    assert "confirm_required_write_skill" in result.risk_flags


def test_missing_why_1s_thread_pass_is_denied():
    gate = PolicyGate()
    tp = _valid_thread_pass()
    tp.pop("why_1s")

    result = gate.evaluate(tp, _valid_action_card())

    assert result.decision == "deny"
    assert "missing_why_1s_thread_pass" in result.risk_flags


def test_missing_why_1s_action_card_is_denied():
    gate = PolicyGate()
    card = _valid_action_card()
    card["why_1s"] = ""

    result = gate.evaluate(_valid_thread_pass(), card)

    assert result.decision == "deny"
    assert "missing_why_1s_action_card" in result.risk_flags


def test_deterministic_overwrites_apply_only_for_whitelisted_keys():
    gate = PolicyGate()
    card = _valid_action_card()

    result = gate.evaluate(
        _valid_thread_pass(),
        card,
        deterministic_overwrites={
            "deterministic.seed": "123",
            "deterministic.forbidden": "x",
            "other.key": "ignored",
        },
    )

    assert result.action_card["deterministic"]["seed"] == "123"
    assert "forbidden" not in result.action_card["deterministic"]
    assert "deterministic_overwrite_applied" in result.risk_flags
    assert "deterministic_overwrite_blocked" in result.risk_flags


def test_risk_flags_are_deterministic_and_overwrite_input():
    gate = PolicyGate()
    tp = _valid_thread_pass()
    card = _valid_action_card()
    card["action"] = "send"
    card["skill"] = "write.file"
    card["risk_flags"] = ["z", "a", "not_used"]

    result1 = gate.evaluate(tp, copy.deepcopy(card))
    result2 = gate.evaluate(tp, copy.deepcopy(card))

    assert result1.risk_flags == result2.risk_flags
    assert list(result1.action_card["risk_flags"]) == sorted(result1.action_card["risk_flags"])
    assert "not_used" not in result1.action_card["risk_flags"]
