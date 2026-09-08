"""Fixtures compartidas de la suite.

El test de salud corre en proceso y no toca la base de datos. Los tests de
persistencia dependen de ``postgres_schema``, que aplica las migraciones
reales sobre PostgreSQL desde base vacía y **falla de forma explícita** si la
base no está accesible: nunca se quedan en verde en silencio.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_database_url
from app.db import get_session
from app.main import app

_REPO_ROOT = Path(__file__).resolve().parent.parent


async def _check_connection() -> None:
    engine = create_async_engine(get_database_url())
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


def _run_alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session")
def postgres_schema() -> None:
    """Deja PostgreSQL migrado desde base vacía para toda la sesión de tests."""

    try:
        asyncio.run(_check_connection())
    except (SQLAlchemyError, OSError) as exc:
        pytest.fail(
            f"PostgreSQL no está accesible en {get_database_url()!r} ({exc}). "
            "Levántalo con 'docker compose up -d' antes de correr los tests de "
            "persistencia.",
            pytrace=False,
        )

    _run_alembic("downgrade", "base")
    _run_alembic("upgrade", "head")


@pytest_asyncio.fixture
async def db_session(postgres_schema: None) -> AsyncIterator[AsyncSession]:
    """Cede una sesión async cuya transacción se revierte al acabar el test.

    Cada test trabaja dentro de una transacción envolvente que se descarta al
    final, de modo que lo que escriba no se ve desde otros tests.
    """

    engine = create_async_engine(get_database_url())
    try:
        async with engine.connect() as conn:
            transaccion = await conn.begin()
            session = AsyncSession(
                bind=conn,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )
            try:
                yield session
            finally:
                await session.close()
                await transaccion.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client(postgres_schema: None) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente HTTP contra la app ASGI.

    La dependencia ``get_session`` se sustituye por una ligada a un engine
    efímero propio del test, para no tocar el engine cacheado de la aplicación
    ni arrastrarlo entre bucles de eventos.
    """

    engine = create_async_engine(get_database_url())
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _session_override() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _session_override
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_session, None)
        await engine.dispose()
