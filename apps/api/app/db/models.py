from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScriptVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    scripts: Mapped[list[Script]] = relationship(back_populates="owner")
    runs: Mapped[list[ScriptRun]] = relationship(back_populates="triggered_by")


class Script(Base):
    __tablename__ = "scripts"
    __table_args__ = (
        Index("ix_scripts_owner_id_updated_at", "owner_id", "updated_at"),
        Index("ix_scripts_visibility", "visibility"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    source_code: Mapped[str] = mapped_column(Text(), nullable=False)
    visibility: Mapped[ScriptVisibility] = mapped_column(
        Enum(ScriptVisibility, name="script_visibility"),
        default=ScriptVisibility.PRIVATE,
        nullable=False,
    )
    tags: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="scripts")
    runs: Mapped[list[ScriptRun]] = relationship(back_populates="script")


class ScriptRun(Base):
    __tablename__ = "script_runs"
    __table_args__ = (
        Index("ix_script_runs_script_id_started_at", "script_id", "started_at"),
        Index("ix_script_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    triggered_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"),
        default=RunStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]
    logs: Mapped[str | None] = mapped_column(Text())

    script: Mapped[Script] = relationship(back_populates="runs")
    triggered_by: Mapped[User | None] = relationship(back_populates="runs")
