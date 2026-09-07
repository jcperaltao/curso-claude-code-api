"""Resolución de la configuración de acceso a datos desde el entorno.

Este módulo solo calcula la cadena de conexión; no crea el engine ni abre
conexiones al importarse.
"""

from __future__ import annotations

import os
from functools import lru_cache

_DEFAULTS = {
    "POSTGRES_USER": "taskflow",
    "POSTGRES_PASSWORD": "taskflow_local_pw",
    "POSTGRES_DB": "taskflow",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
}


def _compose_database_url() -> str:
    """Compone la URL desde las variables ``POSTGRES_*``.

    Usa los mismos valores por defecto que ``compose.yaml`` y ``.env.example``,
    de modo que ``docker compose up -d`` basta para trabajar en local sin
    ``.env``.
    """

    parts = {key: os.environ.get(key, default) for key, default in _DEFAULTS.items()}
    return (
        "postgresql+asyncpg://"
        f"{parts['POSTGRES_USER']}:{parts['POSTGRES_PASSWORD']}"
        f"@{parts['POSTGRES_HOST']}:{parts['POSTGRES_PORT']}/{parts['POSTGRES_DB']}"
    )


@lru_cache
def get_database_url() -> str:
    """Devuelve la cadena de conexión async a PostgreSQL.

    Prioridad: ``DATABASE_URL`` explícito y, si falta, la composición desde
    ``POSTGRES_*``.
    """

    return os.environ.get("DATABASE_URL") or _compose_database_url()
