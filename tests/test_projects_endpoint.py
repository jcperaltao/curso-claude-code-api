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


async def test_listar_proyectos_devuelve_200_ordenado_por_id(
    api_client: httpx.AsyncClient,
) -> None:
    creados = []
    for nombre in ("Casa", "Trabajo", "Jardín"):
        respuesta = await api_client.post("/projects", json={"name": nombre})
        creados.append(respuesta.json()["id"])

    response = await api_client.get("/projects")

    assert response.status_code == 200
    cuerpo = response.json()
    assert isinstance(cuerpo, list)
    assert [proyecto["id"] for proyecto in cuerpo] == sorted(creados)


async def test_listar_proyectos_orden_estable_entre_llamadas(
    api_client: httpx.AsyncClient,
) -> None:
    await api_client.post("/projects", json={"name": "Casa"})
    await api_client.post("/projects", json={"name": "Trabajo"})

    primera = (await api_client.get("/projects")).json()
    segunda = (await api_client.get("/projects")).json()

    assert [proyecto["id"] for proyecto in primera] == [
        proyecto["id"] for proyecto in segunda
    ]


async def test_obtener_proyecto_por_id_devuelve_200(
    api_client: httpx.AsyncClient,
) -> None:
    creado = (
        await api_client.post(
            "/projects", json={"name": "Casa", "description": "Tareas"}
        )
    ).json()

    response = await api_client.get(f"/projects/{creado['id']}")

    assert response.status_code == 200
    assert response.json() == creado


async def test_obtener_proyecto_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.get("/projects/999999")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


async def test_actualizar_solo_name_no_toca_description(
    api_client: httpx.AsyncClient,
) -> None:
    creado = (
        await api_client.post(
            "/projects", json={"name": "Casa", "description": "Tareas"}
        )
    ).json()

    response = await api_client.patch(
        f"/projects/{creado['id']}", json={"name": "Casa Nueva"}
    )

    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["name"] == "Casa Nueva"
    assert cuerpo["description"] == "Tareas"


async def test_actualizar_solo_description_no_toca_name(
    api_client: httpx.AsyncClient,
) -> None:
    creado = (
        await api_client.post(
            "/projects", json={"name": "Casa", "description": "Tareas"}
        )
    ).json()

    response = await api_client.patch(
        f"/projects/{creado['id']}", json={"description": "Otra cosa"}
    )

    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["name"] == "Casa"
    assert cuerpo["description"] == "Otra cosa"


async def test_actualizar_proyecto_inexistente_devuelve_404(
    api_client: httpx.AsyncClient,
) -> None:
    response = await api_client.patch("/projects/999999", json={"name": "X"})

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}
