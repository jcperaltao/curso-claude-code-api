"""Endpoints de Proyectos contra PostgreSQL.

Cubre la matriz mínima del contrato para la sección Proyectos: CRUD feliz,
ids inexistentes, orden estable y esquema de respuesta exacto.
"""

from __future__ import annotations

import httpx


async def test_crear_proyecto_devuelve_201_y_el_recurso(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.post("/projects", json={"name": "Casa"})

    assert response.status_code == 201
    cuerpo = response.json()
    assert cuerpo["name"] == "Casa"
    assert cuerpo["description"] is None
    assert isinstance(cuerpo["id"], int)


async def test_crear_proyecto_esquema_exacto(api_client: httpx.AsyncClient) -> None:
    response = await api_client.post(
        "/projects", json={"name": "Casa", "description": "Tareas domésticas"}
    )

    cuerpo = response.json()
    assert set(cuerpo) == {"id", "name", "description"}
    assert cuerpo["description"] == "Tareas domésticas"
