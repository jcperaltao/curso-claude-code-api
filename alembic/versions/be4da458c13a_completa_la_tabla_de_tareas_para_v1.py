"""completa la tabla de tareas para v1

Añade a ``tasks`` las columnas que le faltaban para Tareas v1: ``title``
(obligatorio), ``description`` (opcional) y ``state_id`` (obligatorio, clave
foránea a ``states.id``). La tabla está vacía en todo entorno existente, así
que las columnas ``NOT NULL`` se añaden sin ``server_default``.

``downgrade`` elimina las tres columnas en orden inverso.

Revision ID: be4da458c13a
Revises: 812c17059bbc
Create Date: 2026-09-13 17:59:46.046323

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be4da458c13a"
down_revision: str | Sequence[str] | None = "812c17059bbc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Añade ``title``, ``description`` y ``state_id`` a ``tasks``."""

    op.add_column("tasks", sa.Column("title", sa.String(), nullable=False))
    op.add_column("tasks", sa.Column("description", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("state_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_tasks_state_id_states",
        "tasks",
        "states",
        ["state_id"],
        ["id"],
    )


def downgrade() -> None:
    """Elimina ``state_id``, ``description`` y ``title`` de ``tasks``."""

    op.drop_constraint("fk_tasks_state_id_states", "tasks", type_="foreignkey")
    op.drop_column("tasks", "state_id")
    op.drop_column("tasks", "description")
    op.drop_column("tasks", "title")
