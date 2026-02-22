"""SQLAlchemy models for Abschnitt 8 schema."""

from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    projects: Mapped[List[Project]] = relationship(back_populates="owner")
    runs: Mapped[List[Run]] = relationship(back_populates="triggered_by")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("owner_id", "slug", name="uq_projects_owner_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    owner: Mapped[User] = relationship(back_populates="projects")
    scripts: Mapped[List[Script]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Script(Base, TimestampMixin):
    __tablename__ = "scripts"
    __table_args__ = (Index("ix_scripts_project_name", "project_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    language: Mapped[str] = mapped_column(String(40), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    project: Mapped[Project] = relationship(back_populates="scripts")
    versions: Mapped[List[ScriptVersion]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )
    run_logs: Mapped[List[Run]] = relationship(back_populates="script")


class ScriptVersion(Base):
    __tablename__ = "script_versions"
    __table_args__ = (UniqueConstraint("script_id", "version", name="uq_script_versions_script_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    script: Mapped[Script] = relationship(back_populates="versions")


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_script_started", "script_id", "started_at"),
        Index("ix_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    triggered_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    output: Mapped[str | None] = mapped_column(Text)

    script: Mapped[Script] = relationship(back_populates="run_logs")
    triggered_by: Mapped[User | None] = relationship(back_populates="runs")
