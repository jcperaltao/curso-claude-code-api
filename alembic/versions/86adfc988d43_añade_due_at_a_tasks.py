"""añade due_at a tasks

Añade a ``tasks`` la columna ``due_at`` (v2: Fechas Límite), opcional, con
zona horaria (``TIMESTAMP WITH TIME ZONE``). Nula por defecto: omitirla
conserva compatibilidad con las tareas creadas en v1.

``downgrade`` elimina la columna.

Revision ID: 86adfc988d43
Revises: be4da458c13a
Create Date: 2026-09-13 18:22:48.396820

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "86adfc988d43"
down_revision: str | Sequence[str] | None = "be4da458c13a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Añade ``due_at`` (nullable) a ``tasks``."""

    op.add_column(
        "tasks", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Elimina ``due_at`` de ``tasks``."""

    op.drop_column("tasks", "due_at")
