"""catalogo de estados

Crea la tabla ``states`` y siembra el catálogo cerrado
(``PENDIENTE``, ``EN_CURSO``, ``BLOQUEADA``, ``HECHA``) en el orden que fija
el contrato. El seed es idempotente: ``ON CONFLICT (code) DO NOTHING`` deja
lo mismo tras ejecutarse una o varias veces.

``downgrade`` elimina la tabla, y con ella el catálogo sembrado.

Revision ID: 13125b9918d2
Revises: 03c6bd17971f
Create Date: 2026-09-07 20:03:30.618509

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "13125b9918d2"
down_revision: str | Sequence[str] | None = "03c6bd17971f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# El catálogo va literal en la migración: no se importa de app.models para que
# la migración quede congelada aunque el modelo evolucione.
_CATALOGO = ("PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA")


def upgrade() -> None:
    """Crea ``states`` y siembra el catálogo de forma idempotente."""

    states = op.create_table(
        "states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    filas = [
        {"code": code, "position": posicion}
        for posicion, code in enumerate(_CATALOGO, start=1)
    ]
    op.get_bind().execute(
        pg_insert(states).values(filas).on_conflict_do_nothing(index_elements=["code"])
    )


def downgrade() -> None:
    """Elimina ``states`` (y el catálogo sembrado)."""

    op.drop_table("states")
