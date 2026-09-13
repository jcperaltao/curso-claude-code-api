# TaskFlow API

API del curso: FastAPI gestionada con [uv](https://docs.astral.sh/uv/), Python
3.12 y persistencia en PostgreSQL (SQLAlchemy async + Alembic). El
comportamiento observable —endpoints, esquemas, códigos de estado— es el que
fija [`docs/contrato-api.md`](docs/contrato-api.md).

La aplicación ASGI se expone como `app.main:app`.

## Requisitos

- Python 3.12 (serie 3.12.x)
- uv
- Docker con Compose

## Puesta en marcha

Todos los comandos se ejecutan desde la raíz del repositorio, en este orden:

```bash
# 1. Instalar dependencias exactas desde el lockfile
uv sync --locked
```

```bash
# 2. Levantar PostgreSQL (servicio db)
docker compose up -d
```

```bash
# 3. Aplicar las migraciones
uv run alembic upgrade head
```

```bash
# 4. Servir la API en local
uv run uvicorn app.main:app --reload
```

Con la API en marcha, comprueba la salud:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

5. Prueba un endpoint con `api.http`.

[`api.http`](api.http), en la raíz del repositorio, tiene una petición por
cada método y ruta del contrato, encadenadas en el orden en que se pueden
ejecutar (cada una usa el resultado de la anterior). Ábrelo con un cliente
que entienda archivos `.http` — por ejemplo la extensión
[REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
de VS Code — y ejecuta el primer bloque (`GET /health`) con "Send Request";
el resto sigue en orden desde ahí.

[`openapi.json`](openapi.json), en la raíz del repositorio, es la
especificación OpenAPI de la API, exportada sin levantar el servidor ni
tocar la base de datos. Se regenera así:

```bash
uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))" > openapi.json
```

Cuando termines, para PostgreSQL:

```bash
docker compose down
```

## Migraciones

Se bajan igual que se suben: `uv run alembic downgrade -1` revierte la
última revisión aplicada y `uv run alembic downgrade base` deja la base en el
estado previo a la primera migración.

## Desarrollo

```bash
# Ejecutar los tests
uv run pytest -q

# Pasar el linter
uv run ruff check .
```

## Configuración

`compose.yaml` trae valores por defecto locales seguros, así que
`docker compose` funciona sin `.env`. Para personalizar las credenciales de
PostgreSQL, copia `.env.example` a `.env` y edítalo:

```bash
cp .env.example .env
```

Variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`.
