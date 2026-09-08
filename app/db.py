"""Engine async, fábrica de sesiones y base declarativa para PostgreSQL.

El engine y la fábrica de sesiones se crean de forma perezosa: importar este
módulo no abre conexiones ni crea esquema.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_database_url


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos del dominio."""


@lru_cache
def get_engine() -> AsyncEngine:
    """Devuelve el engine async, creándolo la primera vez que se pide."""

    return create_async_engine(get_database_url())


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Devuelve la fábrica de sesiones async ligada al engine."""

    return async_sessionmaker(get_engine(), expire_on_commit=False)
