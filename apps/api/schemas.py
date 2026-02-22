from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTaskPayload:
    task_name: str
    priority: int

    def __post_init__(self) -> None:
        if not self.task_name:
            raise ValueError("task_name cannot be empty")
        if self.priority < 1 or self.priority > 5:
            raise ValueError("priority must be between 1 and 5")
