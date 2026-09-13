"""Endpoints de Tareas v1 contra PostgreSQL.

Cubre la matriz mínima del contrato para la sección "Tareas v1": CRUD feliz,
ids inexistentes, proyecto/estado inexistente al crear, título vacío y
espacios ASCII, filtros solos y combinados, orden estable y esquema de
respuesta exacto.
"""

from __future__ import annotations

import httpx


async def _crear_proyecto(api_client: httpx.AsyncClient, name: str = "Casa") -> int:
    respuesta = await api_client.post("/projects", json={"name": name})
    return respuesta.json()["id"]


async def _obtener_state_ids(api_client: httpx.AsyncClient) -> list[int]:
    estados = (await api_client.get("/states")).json()
    return [estado["id"] for estado in estados]


async def test_crear_tarea_devuelve_201_y_el_recurso(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={"title": "Regar las plantas", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 201
    cuerpo = response.json()
    assert cuerpo["title"] == "Regar las plantas"
    assert cuerpo["description"] is None
    assert cuerpo["project_id"] == project_id
    assert cuerpo["state_id"] == state_id
    assert isinstance(cuerpo["id"], int)


async def test_crear_tarea_esquema_exacto(api_client: httpx.AsyncClient) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={
            "title": "Regar",
            "description": "Cada dos días",
            "project_id": project_id,
            "state_id": state_id,
        },
    )

    cuerpo = response.json()
    assert set(cuerpo) == {"id", "title", "description", "project_id", "state_id"}
    assert cuerpo["description"] == "Cada dos días"


async def test_crear_tarea_recorta_espacios_del_titulo(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={"title": "  Regar las plantas  ", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Regar las plantas"


async def test_crear_tarea_con_titulo_vacio_devuelve_422(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={"title": "", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


async def test_crear_tarea_con_titulo_solo_espacios_ascii_devuelve_422(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={"title": "   ", "project_id": project_id, "state_id": state_id},
    )

    assert response.status_code == 422
    assert "detail" in response.json()


async def test_crear_tarea_con_proyecto_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    state_id = (await _obtener_state_ids(api_client))[0]

    response = await api_client.post(
        "/tasks",
        json={"title": "Regar", "project_id": 999999, "state_id": state_id},
    )

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


async def test_crear_tarea_con_estado_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)

    response = await api_client.post(
        "/tasks",
        json={"title": "Regar", "project_id": project_id, "state_id": 999999},
    )

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
