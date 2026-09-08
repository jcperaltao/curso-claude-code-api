"""`GET /states` sirve el catálogo desde PostgreSQL.

Cubre la matriz mínima del contrato para la sección Estados: código 200,
lista en la raíz, esquema exacto (``id`` y ``code``, ni uno más) y orden
estable entre llamadas idénticas.
"""

from __future__ import annotations

import httpx

from app.models import STATE_CODES


async def test_states_devuelve_200_y_el_catalogo(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/states")

    assert response.status_code == 200
    cuerpo = response.json()
    assert isinstance(cuerpo, list)
    assert [estado["code"] for estado in cuerpo] == list(STATE_CODES)


async def test_states_esquema_exacto(api_client: httpx.AsyncClient) -> None:
    cuerpo = (await api_client.get("/states")).json()

    assert cuerpo, "el catálogo no debería venir vacío"
    for estado in cuerpo:
        assert set(estado) == {"id", "code"}
        assert isinstance(estado["id"], int)
        assert isinstance(estado["code"], str)


async def test_states_orden_estable_entre_llamadas(
    api_client: httpx.AsyncClient,
) -> None:
    primera = (await api_client.get("/states")).json()
    segunda = (await api_client.get("/states")).json()

    assert [estado["id"] for estado in primera] == [
        estado["id"] for estado in segunda
    ]
