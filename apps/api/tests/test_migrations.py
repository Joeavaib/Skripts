from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_upgrades_to_head(tmp_path) -> None:
    database_path = tmp_path / "test.db"
    database_url = f"sqlite:///{database_path}"

    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.set_main_option("prepend_sys_path", str(PROJECT_ROOT))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert {"users", "scripts", "script_runs"}.issubset(set(inspector.get_table_names()))

    scripts_indexes = {index["name"] for index in inspector.get_indexes("scripts")}
    script_runs_indexes = {index["name"] for index in inspector.get_indexes("script_runs")}

    assert "ix_scripts_owner_id_updated_at" in scripts_indexes
    assert "ix_scripts_visibility" in scripts_indexes
    assert "ix_script_runs_script_id_started_at" in script_runs_indexes
    assert "ix_script_runs_status" in script_runs_indexes
