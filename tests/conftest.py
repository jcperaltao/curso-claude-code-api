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
    AsyncConnection,
    AsyncSession,
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
async def _connection(postgres_schema: None) -> AsyncIterator[AsyncConnection]:
    """Conexión única por test, con una transacción que se revierte al final.

    ``db_session`` y ``api_client`` comparten esta misma conexión: lo que uno
    escribe (con o sin ``commit()``) lo ve el otro dentro del mismo test, y
    todo se revierte junto al acabar, sin dejar rastro en la base compartida.
    """

    engine = create_async_engine(get_database_url())
    try:
        async with engine.connect() as conn:
            transaccion = await conn.begin()
            try:
                yield conn
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    """Cede una sesión async ligada a la conexión de prueba del test.

    Usa un savepoint propio sobre la transacción envolvente de ``_connection``,
    así que lo que escriba se revierte con ella al final del test.
    """

    session = AsyncSession(
        bind=_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def api_client(_connection: AsyncConnection) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente HTTP contra la app ASGI.

    La dependencia ``get_session`` se sustituye por una sesión ligada a la
    misma conexión de prueba que ``db_session`` (savepoint propio, igual
    patrón), en vez de crear un engine y una sesión nuevos por request: así
    un ``commit()`` del endpoint no persiste de verdad en la base compartida,
    y una fila que un test inserte con ``db_session`` es visible para las
    peticiones que ese mismo test haga con este cliente.
    """

    session = AsyncSession(
        bind=_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async def _session_override() -> AsyncIterator[AsyncSession]:
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
        await session.close()
