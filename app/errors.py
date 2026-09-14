"""Manejo centralizado de errores HTTP de negocio.

Toda referencia a un recurso inexistente (404) o a un conflicto de negocio
(409) pasa por aquí, para que la forma de la respuesta
—``{"detail": "<mensaje>"}``— quede en un solo lugar.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import NoReturn

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base

# Categorías Unicode sin carácter visible: control, formato y separadores de
# línea, párrafo y espacio. Un título que, tras recortar los extremos, solo
# contenga caracteres de estas categorías no deja nada visible.
_CATEGORIAS_INVISIBLES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


class ErrorDetail(BaseModel):
    """Forma estable de un error de negocio: ``{"detail": "<mensaje>"}``."""

    detail: str


def normalizar_titulo(valor: str) -> str:
    """Recorta los extremos y rechaza un título sin ningún carácter visible."""

    recortado = valor.strip()
    if all(unicodedata.category(c) in _CATEGORIAS_INVISIBLES for c in recortado):
        raise ValueError("El título no puede estar vacío")
    return recortado


def validar_due_at(valor: datetime | None) -> datetime | None:
    """Rechaza una fecha sin zona horaria: es ambigua y el contrato no la
    supone por su cuenta."""

    if valor is not None and valor.tzinfo is None:
        raise ValueError("due_at debe incluir zona horaria")
    return valor


async def obtener_o_404[ModeloT: Base](
    modelo: type[ModeloT], id_: int, session: AsyncSession, mensaje: str
) -> ModeloT:
    """Devuelve la fila pedida por id, o corta con 404 si no existe."""

    instancia = await session.get(modelo, id_)
    if instancia is None:
        raise HTTPException(status_code=404, detail=mensaje)
    return instancia


def conflicto(mensaje: str) -> NoReturn:
    """Corta con 409: un conflicto de negocio."""

    raise HTTPException(status_code=409, detail=mensaje)
