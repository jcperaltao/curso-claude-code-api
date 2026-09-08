"""baseline vacia

Punto de partida del historial de migraciones. No crea ni modifica esquema:
solo deja registrada la revision base en ``alembic_version`` para que
``upgrade``/``downgrade`` tengan un extremo conocido.

Revision ID: 03c6bd17971f
Revises:
Create Date: 2026-09-07 20:01:06.969625

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "03c6bd17971f"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Sin cambios de esquema."""


def downgrade() -> None:
    """Sin cambios de esquema."""
