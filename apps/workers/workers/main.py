from __future__ import annotations


def run_job() -> str:
    return "workers idle"


def run() -> None:
    print(run_job())


if __name__ == "__main__":
    run()
