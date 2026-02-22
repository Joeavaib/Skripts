"""Async SQLAlchemy 2.x engine/session setup."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./app.db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine(database_url: str | None = None, echo: bool = False) -> AsyncEngine:
    return create_async_engine(database_url or get_database_url(), echo=echo, future=True)


engine = create_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
