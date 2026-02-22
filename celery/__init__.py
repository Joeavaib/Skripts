from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class CeleryConfig(dict):
    def __getattr__(self, item: str) -> Any:
        return self[item]

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


@dataclass
class Celery:
    name: str
    conf: CeleryConfig = field(default_factory=CeleryConfig)

    def __post_init__(self) -> None:
        self.conf.setdefault("beat_schedule", {})

    def autodiscover_tasks(self, modules: list[str]) -> None:
        self._autodiscovered_modules = modules

    def task(self, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            func._celery_task_name = name or func.__name__
            return func

        return decorator
