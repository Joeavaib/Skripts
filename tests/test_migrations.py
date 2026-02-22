from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_expected_schema(tmp_path: Path) -> None:
    db_file = tmp_path / "migration_test.db"
    alembic_ini = Path("apps/api/alembic.ini").resolve()
    script_location = Path("apps/api/migrations").resolve()

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_file}")
    inspector = inspect(engine)

    tables = set(inspector.get_table_names())
    assert tables == {"users", "projects", "scripts", "script_versions", "runs"}

    assert any(index["name"] == "ix_users_email" for index in inspector.get_indexes("users"))
    assert any(index["name"] == "ix_scripts_project_name" for index in inspector.get_indexes("scripts"))
    assert any(index["name"] == "ix_runs_status" for index in inspector.get_indexes("runs"))
