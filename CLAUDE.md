# CLAUDE.md

Guía para Claude Code (claude.ai/code) en este repositorio. Recoge solo lo que
aplica a cualquier tarea; el detalle vive en los documentos citados.

## Fuentes de verdad

- **Comportamiento observable** (códigos de estado, esquemas de respuesta,
  orden de listas, normalización de texto, forma del error): `docs/contrato-api.md`.
  Solo se modifica cuando el ticket dice explícitamente que cambia el contrato,
  y en un commit separado antes de tocar tests o código.
- **Decisiones de ingeniería del equipo**: `docs/decisiones-ingenieria.md`.
- **Comandos canónicos del repositorio**: `README.md`.

## Comandos

Desde la raíz del repositorio.

```bash
uv sync --locked        # instalar dependencias exactas desde el lockfile
uv run pytest -q        # ejecutar los tests
uv run ruff check .     # pasar el linter
```

## Persistencia

- Los tests que ejercitan persistencia corren contra **PostgreSQL, no SQLite**:
  SQLite no reproduce las mismas restricciones, tipos ni migraciones.

## `.env`

- Puede contener secretos. No lo abras, muestres, edites ni añadas a Git.
  `.env.example` es la única fuente permitida para nombres de variables.
