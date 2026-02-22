from policy.gate import is_action_allowed


def test_admin_gate_allows_write_action() -> None:
    permissions = {"admin": {"read", "write"}, "viewer": {"read"}}

    assert is_action_allowed("admin", "write", permissions)
    assert not is_action_allowed("viewer", "write", permissions)
