"""proyectos y tabla minima de tareas

Crea ``projects`` (``id``, ``name`` obligatorio, ``description`` opcional) y
``tasks`` (``id``, ``project_id`` con clave foránea a ``projects.id``).

``tasks`` es mínima a propósito: solo lo que el ``409`` de
``DELETE /projects/{id}`` necesita para comprobar si un proyecto tiene
tareas. El plan de Tareas añade el resto de columnas sobre esta misma tabla,
no la crea de nuevo.

``downgrade`` elimina ``tasks`` antes que ``projects``, por la clave foránea.

Revision ID: 812c17059bbc
Revises: 13125b9918d2
Create Date: 2026-09-10 23:06:07.219177

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "812c17059bbc"
down_revision: str | Sequence[str] | None = "13125b9918d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea ``projects`` y, sobre ella, la tabla mínima ``tasks``."""

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
    )


def downgrade() -> None:
    """Elimina ``tasks`` y luego ``projects``, por la clave foránea."""

    op.drop_table("tasks")
    op.drop_table("projects")
