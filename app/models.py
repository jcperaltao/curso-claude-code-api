"""Modelos del dominio de TaskFlow.

Importar este módulo registra las tablas en ``Base.metadata``; no crea
esquema ni abre conexiones.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

# Catálogo cerrado de estados, en el orden que fija el contrato. La posición
# de cada código en esta tupla es su campo de orden en la tabla.
STATE_CODES: tuple[str, ...] = ("PENDIENTE", "EN_CURSO", "BLOQUEADA", "HECHA")


class State(Base):
    """Estado del catálogo cerrado.

    No se crea ni se borra desde la API: existe antes de la primera petición,
    sembrado por una migración idempotente.
    """

    __tablename__ = "states"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(unique=True)
    position: Mapped[int] = mapped_column()


class Project(Base):
    """Proyecto: agrupa tareas. Ver ``docs/contrato-api.md``, sección Proyectos."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(default=None)


class Task(Base):
    """Tarea: unidad de trabajo de un proyecto. Ver ``docs/contrato-api.md``,
    secciones "Tareas v1" y "Tareas v2: Fechas Límite".
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(default=None)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"))
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
