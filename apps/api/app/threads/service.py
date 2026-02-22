from __future__ import annotations

from typing import Any, Protocol

from packages.schemas.validator import validate_planner_bundle


class PlannerOutputRepository(Protocol):
    def save_planner_outputs(
        self,
        *,
        thread_pass: dict[str, Any],
        action_cards: list[dict[str, Any]],
        skill_registry: dict[str, Any],
        timeline_events: list[dict[str, Any]],
    ) -> None: ...


def persist_planner_outputs(
    repository: PlannerOutputRepository,
    *,
    thread_pass: dict[str, Any],
    action_cards: list[dict[str, Any]],
    skill_registry: dict[str, Any],
    timeline_events: list[dict[str, Any]],
) -> None:
    """Validate planner artifacts before persistence.

    Validation is a mandatory gate and will raise before any repository write
    happens when payloads violate schema contracts.
    """

    validate_planner_bundle(
        thread_pass=thread_pass,
        action_cards=action_cards,
        skill_registry=skill_registry,
        timeline_events=timeline_events,
    )

    repository.save_planner_outputs(
        thread_pass=thread_pass,
        action_cards=action_cards,
        skill_registry=skill_registry,
        timeline_events=timeline_events,
    )
