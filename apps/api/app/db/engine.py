from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_POOL_PRE_PING = True


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create a SQLAlchemy 2.x async engine."""

    return create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=DEFAULT_POOL_PRE_PING,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to ``engine``."""

    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a managed async session."""

    async with session_factory() as session:
        yield session

