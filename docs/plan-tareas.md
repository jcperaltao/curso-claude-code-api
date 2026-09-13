# Plan: Tareas (v1 completas, v2 Fechas Límite)

Plan de referencia para las secciones "Tareas v1" y "Tareas v2: Fechas Límite"
de `docs/contrato-api.md`.

Cada incremento es un commit que se confirma solo; al terminar uno se para y
se espera aprobación antes del siguiente.

## Fuentes

- `docs/contrato-api.md` — secciones "Tareas v1" y "Tareas v2: Fechas Límite"
  (campos, endpoints, `due_at` opcional con zona horaria normalizado a UTC,
  `422` si falta la zona, `GET /tasks?overdue=true`), "Convenciones"
  (`404`/`409`/`422`, error `{"detail": "<mensaje>"}`), "Orden de las listas"
  (`GET /tasks` por `id` ascendente, también con filtros aplicados),
  "Esquemas de Respuesta" (`due_at` serializado siempre en UTC con `Z`, sin
  microsegundos y sin desplazamiento; un campo opcional ausente se devuelve
  como `null`) y "Matriz Mínima de Tests" (`due_at` omitido, válido, sin zona,
  vencido, futuro y tarea hecha).
- `docs/decisiones-ingenieria.md` — tests de persistencia contra PostgreSQL,
  migraciones probadas en ambos sentidos, una capacidad nueva empieza por un
  test que falla, no se debilita un test existente para ponerlo en verde.
- `README.md` — comandos canónicos que usa cada Comprobación.
- `CLAUDE.md` — el contrato como única fuente del comportamiento observable;
  `.env` no se abre ni se edita.
- Estado real del repositorio: **Tareas v1 ya está completa.**
  `app/models.py` define `Task` con `id`, `project_id`, `title`,
  `description`, `state_id` (sin `due_at`). `app/main.py` expone
  `POST/GET/PATCH/DELETE /tasks` y `GET /tasks/{id}`, con validación de
  proyecto/estado, normalización de título y filtros por `project_id` y
  `state_id`, solos o combinados. La migración `be4da458c13a` (head actual)
  añadió `title`, `description` y `state_id` a `tasks`. `tests/test_tasks_endpoint.py`
  cubre la matriz mínima de v1. No existe columna `due_at`, ni filtro
  `overdue`, ni ninguna migración que los añada.

## Decisiones tomadas

- **`overdue` es un filtro adicional, no un reemplazo**: sigue el mismo
  patrón que `project_id` y `state_id` en `GET /tasks` — un parámetro de
  consulta opcional que, cuando está ausente o no vale `true`, no se aplica.
  El contrato solo define comportamiento para `overdue=true`; ningún otro
  valor tiene un significado especial, y se combina con `project_id` y
  `state_id` igual que estos se combinan entre sí.
- **Columna `due_at`**: `TIMESTAMP WITH TIME ZONE` (`DateTime(timezone=True)`
  en SQLAlchemy), nullable, sin `server_default`. Es la representación directa
  de "con zona horaria y normalizado a UTC" que pide el contrato; Postgres
  almacena el instante y lo devuelve normalizado, sin que la aplicación tenga
  que reconstruir el desplazamiento original.

## Fuera de alcance

- Rehacer Tareas v1: ya está implementada y probada; este plan no la toca.
- Recordatorios, scheduler, zona preferida del usuario y cambio automático de
  estado: el contrato los excluye explícitamente en "Tareas v2".
- Cualquier significado para `overdue` distinto de `true` (por ejemplo,
  `overdue=false` como "solo no vencidas"): no está en el contrato.
- Skills, hooks y verificación automatizada del propio flujo de Claude Code.

## Incrementos

### Incremento 1 — Columna `due_at` y migración

- `app/models.py`: añade `due_at: Mapped[datetime | None]` a `Task`, con
  `DateTime(timezone=True)` y `default=None`.
- Migración nueva, con `be4da458c13a` como `down_revision`: añade la columna
  `due_at` (nullable) a `tasks`; `downgrade` la elimina.
- **Comprobación:**
  ```bash
  docker compose up -d
  uv run alembic upgrade head
  uv run alembic downgrade -1
  uv run alembic upgrade head
  uv run ruff check .
  ```

### Incremento 2 — `due_at` en `POST`/`PATCH`/`GET /tasks/{id}` y en el esquema de salida

- Test que falla primero: crear una tarea sin `due_at` conserva el
  comportamiento v1 (`due_at` se devuelve como `null`); crear con una fecha
  con zona la persiste y la serializa en UTC con `Z`, sin microsegundos ni
  desplazamiento (por ejemplo, una fecha con offset `-03:00` se devuelve en
  `Z`); crear con una fecha **sin** zona devuelve `422`; `PATCH` acepta
  actualizar `due_at` con las mismas reglas; el esquema de respuesta sigue
  siendo exacto (ahora con `due_at` incluido).
- Después: `TaskCreate`/`TaskUpdate` validan que `due_at`, si llega, tenga
  `tzinfo`; `TaskOut` serializa `due_at` en UTC con `Z` y sin microsegundos
  cuando no es `None`.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```

### Incremento 3 — `GET /tasks?overdue=true`

- Test que falla primero: con tareas vencidas (fecha pasada, estado distinto
  de `HECHA`), futuras, sin `due_at` y vencidas pero en estado `HECHA`, solo
  las vencidas y no `HECHA` aparecen en `overdue=true`; una tarea sin
  `due_at` nunca aparece; `overdue=true` combinado con `project_id` y/o
  `state_id` sigue filtrando por ambos; el orden sigue siendo por `id`
  ascendente y estable entre llamadas idénticas.
- Después: la ruta añade el filtro `due_at < instante de evaluación` y
  `state.code != "HECHA"` cuando `overdue` es `true`.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```
