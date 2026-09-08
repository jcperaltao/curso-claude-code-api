"""La migración deja el catálogo de estados sembrado, ordenado y sin duplicados.

Cubre la matriz mínima del contrato: "El catálogo de estados existe tras
migrar, y migrar dos veces no lo duplica."
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import STATE_CODES, State


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
