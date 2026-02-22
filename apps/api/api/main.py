from __future__ import annotations


def create_app() -> dict[str, str]:
    return {"service": "api", "status": "ok"}


def run() -> None:
    app = create_app()
    print(f"{app['service']} ready ({app['status']})")


if __name__ == "__main__":
    run()
