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
async def test_listar_tareas_devuelve_200_ordenado_por_id(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creadas = []
    for titulo in ("Regar", "Barrer", "Cocinar"):
        respuesta = await api_client.post(
            "/tasks",
            json={"title": titulo, "project_id": project_id, "state_id": state_id},
        )
        creadas.append(respuesta.json()["id"])

    response = await api_client.get("/tasks")

    assert response.status_code == 200
    cuerpo = response.json()
    assert isinstance(cuerpo, list)
    assert [tarea["id"] for tarea in cuerpo] == sorted(creadas)


async def test_listar_tareas_orden_estable_entre_llamadas(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    await api_client.post(
        "/tasks", json={"title": "Regar", "project_id": project_id, "state_id": state_id}
    )
    await api_client.post(
        "/tasks", json={"title": "Barrer", "project_id": project_id, "state_id": state_id}
    )

    primera = (await api_client.get("/tasks")).json()
    segunda = (await api_client.get("/tasks")).json()

    assert [tarea["id"] for tarea in primera] == [tarea["id"] for tarea in segunda]


async def test_listar_tareas_filtra_por_project_id(
    api_client: httpx.AsyncClient,
) -> None:
    project_a = await _crear_proyecto(api_client, "Casa")
    project_b = await _crear_proyecto(api_client, "Trabajo")
    state_id = (await _obtener_state_ids(api_client))[0]
    tarea_a = (
        await api_client.post(
            "/tasks", json={"title": "Regar", "project_id": project_a, "state_id": state_id}
        )
    ).json()["id"]
    await api_client.post(
        "/tasks", json={"title": "Reunión", "project_id": project_b, "state_id": state_id}
    )

    response = await api_client.get("/tasks", params={"project_id": project_a})

    assert response.status_code == 200
    assert [tarea["id"] for tarea in response.json()] == [tarea_a]


async def test_listar_tareas_filtra_por_state_id(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_ids = await _obtener_state_ids(api_client)
    tarea_1 = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_id, "state_id": state_ids[0]},
        )
    ).json()["id"]
    await api_client.post(
        "/tasks",
        json={"title": "Barrer", "project_id": project_id, "state_id": state_ids[1]},
    )

    response = await api_client.get("/tasks", params={"state_id": state_ids[0]})

    assert response.status_code == 200
    assert [tarea["id"] for tarea in response.json()] == [tarea_1]


async def test_listar_tareas_filtros_combinados(
    api_client: httpx.AsyncClient,
) -> None:
    project_a = await _crear_proyecto(api_client, "Casa")
    project_b = await _crear_proyecto(api_client, "Trabajo")
    state_ids = await _obtener_state_ids(api_client)
    objetivo = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_a, "state_id": state_ids[0]},
        )
    ).json()["id"]
    await api_client.post(
        "/tasks",
        json={"title": "Barrer", "project_id": project_a, "state_id": state_ids[1]},
    )
    await api_client.post(
        "/tasks",
        json={"title": "Reunión", "project_id": project_b, "state_id": state_ids[0]},
    )

    response = await api_client.get(
        "/tasks", params={"project_id": project_a, "state_id": state_ids[0]}
    )

    assert response.status_code == 200
    assert [tarea["id"] for tarea in response.json()] == [objetivo]


async def test_obtener_tarea_por_id_devuelve_200(api_client: httpx.AsyncClient) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creada = (
        await api_client.post(
            "/tasks",
            json={
                "title": "Regar",
                "description": "Tarea",
                "project_id": project_id,
                "state_id": state_id,
            },
        )
    ).json()

    response = await api_client.get(f"/tasks/{creada['id']}")

    assert response.status_code == 200
    assert response.json() == creada


async def test_obtener_tarea_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/tasks/999999")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
async def test_actualizar_solo_title_no_toca_description(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creada = (
        await api_client.post(
            "/tasks",
            json={
                "title": "Regar",
                "description": "Tarea",
                "project_id": project_id,
                "state_id": state_id,
            },
        )
    ).json()

    response = await api_client.patch(f"/tasks/{creada['id']}", json={"title": "Regar más"})

    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["title"] == "Regar más"
    assert cuerpo["description"] == "Tarea"


async def test_actualizar_state_id_a_uno_existente(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_ids = await _obtener_state_ids(api_client)
    creada = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_id, "state_id": state_ids[0]},
        )
    ).json()

    response = await api_client.patch(
        f"/tasks/{creada['id']}", json={"state_id": state_ids[1]}
    )

    assert response.status_code == 200
    assert response.json()["state_id"] == state_ids[1]


async def test_actualizar_con_project_id_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creada = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await api_client.patch(
        f"/tasks/{creada['id']}", json={"project_id": 999999}
    )

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


async def test_actualizar_con_state_id_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creada = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await api_client.patch(
        f"/tasks/{creada['id']}", json={"state_id": 999999}
    )

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


async def test_actualizar_con_titulo_vacio_devuelve_422(
    api_client: httpx.AsyncClient,
) -> None:
    project_id = await _crear_proyecto(api_client)
    state_id = (await _obtener_state_ids(api_client))[0]
    creada = (
        await api_client.post(
            "/tasks",
            json={"title": "Regar", "project_id": project_id, "state_id": state_id},
        )
    ).json()

    response = await api_client.patch(f"/tasks/{creada['id']}", json={"title": "   "})

    assert response.status_code == 422


async def test_actualizar_tarea_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.patch("/tasks/999999", json={"title": "X"})

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
