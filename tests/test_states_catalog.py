"""La migración deja el catálogo de estados sembrado, ordenado y sin duplicados.

Cubre la matriz mínima del contrato: "El catálogo de estados existe tras
migrar, y migrar dos veces no lo duplica."
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_database_url
from app.models import STATE_CODES, State

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_alembic(*args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


async def _tabla_states_existe() -> bool:
    engine = create_async_engine(get_database_url())
    try:
        async with engine.connect() as conn:
            marca = await conn.scalar(
                text("SELECT to_regclass('public.states') IS NOT NULL")
            )
            return bool(marca)
    finally:
        await engine.dispose()


async def test_catalogo_presente_y_ordenado(db_session: AsyncSession) -> None:
    resultado = await db_session.execute(
        select(State.code).order_by(State.position, State.id)
    )
    assert tuple(resultado.scalars().all()) == STATE_CODES


async def test_catalogo_sin_duplicados(db_session: AsyncSession) -> None:
    total = await db_session.scalar(select(func.count()).select_from(State))
    distintos = await db_session.scalar(
        select(func.count(func.distinct(State.code)))
    )
    assert total == distintos == len(STATE_CODES)


async def test_reejecutar_el_seed_no_duplica(db_session: AsyncSession) -> None:
    # Reproduce el seed idempotente de la migración 13125b9918d2: volver a
    # ejecutarlo sobre el catálogo ya sembrado no añade filas.
    stmt = (
        pg_insert(State.__table__)
        .values(
            [
                {"code": code, "position": posicion}
                for posicion, code in enumerate(STATE_CODES, start=1)
            ]
        )
        .on_conflict_do_nothing(index_elements=["code"])
    )
    await db_session.execute(stmt)

    total = await db_session.scalar(select(func.count()).select_from(State))
    assert total == len(STATE_CODES)


async def test_bajar_la_migracion_elimina_la_tabla(postgres_schema: None) -> None:
    # El downgrade de 13125b9918d2 ejecuta op.drop_table("states"); el upgrade la
    # repone con su seed. Se restaura head en cualquier caso para no alterar el
    # esquema de sesión que comparten los demás tests.
    assert await _tabla_states_existe() is True

    _run_alembic("downgrade", "03c6bd17971f")
    try:
        assert await _tabla_states_existe() is False
    finally:
        _run_alembic("upgrade", "head")

    assert await _tabla_states_existe() is True
