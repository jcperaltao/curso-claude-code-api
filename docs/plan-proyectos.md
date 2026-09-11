# Plan: Proyectos

Plan de referencia para implementar el recurso **Proyectos**, según la sección
"Proyectos" de `docs/contrato-api.md`.

Cada incremento es un commit que se confirma solo; al terminar uno se para y
se espera aprobación antes del siguiente.

## Fuentes

- `docs/contrato-api.md` — sección "Proyectos" (campos, endpoints, `409` al
  borrar con tareas), "Convenciones" (`404`/`409`/`422`, error
  `{"detail": "<mensaje>"}`, "una referencia a proyecto o estado inexistente
  no se crea implícitamente"), "Normalización de texto" (se aplica solo a
  `title` de tarea), "Orden de las listas" (`GET /projects` por `id`
  ascendente) y "Esquemas de Respuesta" (`{"id":1,"name":"Casa","description":null}`).
- `docs/decisiones-ingenieria.md` — tests de persistencia contra PostgreSQL,
  migraciones probadas en ambos sentidos, una capacidad nueva empieza por un
  test que falla, no se debilita un test existente para ponerlo en verde.
- `README.md` — comandos canónicos que usa cada Comprobación.
- `CLAUDE.md` — el contrato como única fuente del comportamiento observable;
  `.env` no se abre ni se edita.
- Estado real del repositorio: `app/models.py` solo define `State`;
  `app/main.py` solo expone `GET /health` y `GET /states`; la única
  migración de dominio es `13125b9918d2` (catálogo de estados); no existe
  tabla, modelo ni endpoint de Tareas.

## Decisiones tomadas

- **`DELETE /projects/{id}` sin que exista Tareas todavía**: el
  comportamiento acordado (`409` si el proyecto tiene tareas) se implementa
  igual, con una tabla `tasks` mínima (`id`, `project_id`) creada en este
  plan para sostener el chequeo. Lo que hoy no se puede comprobar —el flujo
  completo a través de la API, creando la tarea con `POST /tasks`, que no
  existe todavía— se declara sin probar en el Incremento 5 y en "Fuera de
  alcance". El resto de columnas de `tasks` (`title`, `description`,
  `state_id`, `due_at`) las añade el plan de Tareas, no este.
- **Validación de `name`**: el contrato normaliza `title` de tarea de forma
  explícita ("Se aplica a `title` de tarea", `docs/contrato-api.md`, sección
  "Normalización de texto") y no menciona `name` de Proyecto. Ese alcance es
  literal, no un olvido: `name` solo exige ser una cadena no nula (lo que ya
  impone el tipo en el esquema de entrada); una cadena vacía o solo espacios
  no se rechaza en este plan porque el contrato no lo pide.

## Fuera de alcance

- Los endpoints y el modelo completo de Tareas (`POST/GET/PATCH/DELETE
  /tasks`, normalización de `title`, `due_at`, filtros): solo se crea la
  tabla mínima `tasks` que el `409` de Proyectos necesita.
- Borrado en cascada de tareas al borrar un proyecto: el contrato dice que
  no hay cascada implícita.
- El flujo de extremo a extremo del `409` a través de la API (crear la tarea
  con `POST /tasks` y después borrar el proyecto): no es comprobable hasta
  que exista el plan de Tareas. Aquí el `409` se prueba insertando la fila
  en `tasks` directamente contra la sesión de base de datos.
- Unicidad de `name`: el contrato no la pide y este plan no la añade.
- Skills, hooks y verificación automatizada del propio flujo de Claude Code.

## Incrementos

### Incremento 1 — Modelo, migración y tabla mínima de tareas

- `app/models.py` añade `Project` (`id`, `name: str`, `description: str |
  None`) y una clase `Task` mínima (`id`, `project_id`, con clave foránea a
  `projects.id`), marcada en un comentario como el subconjunto que Proyectos
  necesita para su propio `409`; el plan de Tareas la completa.
- Migración nueva, con `13125b9918d2` como `down_revision`: crea `projects` y
  `tasks` (en ese orden, por la clave foránea); `downgrade` las elimina en
  orden inverso.
- **Comprobación:**
  ```bash
  docker compose up -d
  uv run alembic upgrade head
  uv run alembic downgrade -1
  uv run alembic upgrade head
  uv run ruff check .
  ```

### Incremento 2 — `POST /projects`

- Test que falla primero: `201` con el recurso creado; `description`
  ausente en el cuerpo se devuelve como `null` (no se omite); esquema exacto
  (`id`, `name`, `description`, sin campos de más).
- Después, la ruta que inserta el `Project` y lo serializa con un
  `response_model` estricto, siguiendo el patrón de `StateOut` en
  `app/main.py`.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```

### Incremento 3 — `GET /projects` y `GET /projects/{id}`

- Test que falla primero: `GET /projects` en `200` ordenado por `id`
  ascendente, con dos llamadas idénticas devolviendo el mismo orden;
  `GET /projects/{id}` en `200` para un id existente y `404` con
  `{"detail": "<mensaje>"}` para uno que no existe.
- Después, las dos rutas de lectura sobre `Project`.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```

### Incremento 4 — `PATCH /projects/{id}`

- Test que falla primero: actualización parcial de solo `name`, de solo
  `description`, y `404` si el id no existe.
- Después, la ruta `PATCH` con un esquema de entrada donde ambos campos son
  opcionales y solo se actualiza lo que llega en el cuerpo.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```

### Incremento 5 — `DELETE /projects/{id}`

- Test que falla primero: `204` sin cuerpo cuando el proyecto no tiene
  tareas; `409` con `{"detail": "<mensaje>"}` cuando tiene al menos una,
  insertando esa fila directamente en `tasks` vía `db_session` (no hay
  `POST /tasks` para crearla por la API: el camino por API queda sin probar,
  ver "Fuera de alcance").
- Después, la ruta que comprueba si existe alguna fila en `tasks` con ese
  `project_id` antes de borrar.
- **Comprobación:**
  ```bash
  uv run pytest -q
  uv run ruff check .
  ```
