"""Modelos del dominio de TaskFlow.

Importar este módulo registra las tablas en ``Base.metadata``; no crea
esquema ni abre conexiones.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey
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
    """Tabla mínima de tareas: solo lo que Proyectos necesita para su ``409``
    al borrar un proyecto con tareas. El plan de Tareas añade el resto de
    columnas (``title``, ``description``, ``state_id``, ``due_at``) sobre
    esta base; no crea la tabla de nuevo.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
