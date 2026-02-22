from collections.abc import Mapping


def is_action_allowed(role: str, action: str, permissions: Mapping[str, set[str]]) -> bool:
    allowed_actions = permissions.get(role, set())
    return action in allowed_actions
