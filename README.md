# TaskFlow API

Base de la API del curso: FastAPI gestionada con [uv](https://docs.astral.sh/uv/)
y Python 3.12. Esta entrega solo expone `GET /health`; el resto del
[contrato](docs/contrato-api.md) llega en sesiones posteriores.

La aplicación ASGI se expone como `app.main:app`.

## Requisitos

- Python 3.12 (serie 3.12.x)
- uv
- Docker con Compose

## Recorrido canónico

Todos los comandos se ejecutan desde la raíz del repositorio.

```bash
# 1. Instalar dependencias exactas desde el lockfile
uv sync --locked

# 2. Ejecutar los tests
uv run pytest -q

# 3. Pasar el linter
uv run ruff check .

# 4. Levantar PostgreSQL (servicio db)
docker compose up -d

# 5. Aplicar las migraciones
uv run alembic upgrade head

# 6. Servir la API en local
uv run uvicorn app.main:app --reload

# 7. Parar PostgreSQL al terminar
docker compose down
```

Comprueba la salud con la API en marcha:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## Configuración

`compose.yaml` trae valores por defecto locales seguros, así que
`docker compose` funciona sin `.env`. Para personalizar las credenciales de
PostgreSQL, copia `.env.example` a `.env` y edítalo:

```bash
cp .env.example .env
```

Variables: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`.
