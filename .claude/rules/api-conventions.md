---
paths:
  - "app/**"
---

# Convenciones de la API

Aplica a: `app/` (los endpoints viven en `app/main.py`).

## Esquema de respuesta exacto

- Cada endpoint tiene una clase `<Entidad>Out` que declara los campos exactos que devuelve — ni uno más, ni uno menos — igual que fija `docs/contrato-api.md` en "Esquemas de Respuesta".
- Un campo opcional ausente se serializa como `null`, nunca se omite del JSON (`description`, `due_at`).
- `GET` de colección nunca envuelve la lista en un objeto con metadatos: la respuesta es un array JSON en la raíz.

## Código de estado por tipo de error

- `404` cuando el recurso pedido por id no existe, o cuando una referencia (`project_id`, `state_id`) apunta a algo que no existe — `raise HTTPException(status_code=404, detail="<mensaje>")`, nunca `None` ni un valor sentinela.
- `409` para un conflicto de negocio (borrar un proyecto con tareas) — mismo patrón que el 404, con `detail`.
- `422` para una entrada inválida — nunca se lanza a mano: se señaliza con `raise ValueError("<mensaje>")` dentro de un `@field_validator` de Pydantic, y FastAPI lo traduce.
- Todo error, sea cual sea su origen, mantiene `detail` como clave de primer nivel de la respuesta.

## Colecciones: lista en la raíz y orden estable

- Un `GET` de colección (`/states`, `/projects`, `/tasks`) devuelve una lista JSON en la raíz — nunca `{"items": [...], "total": N}` ni ninguna otra envoltura.
- El orden es estable entre llamadas idénticas: por `id` ascendente para `/projects` y `/tasks`, por el campo de orden del catálogo (y `id` de desempate) para `/states`.
- Un filtro de colección (`project_id`, `state_id`, `overdue`) nunca cambia el criterio de orden, solo reduce el conjunto.

## Un campo nuevo se añade en tres capas

- **Migración**: columna nueva en `alembic/versions/`, con `upgrade` y `downgrade` simétricos, antes de tocar el modelo.
- **Esquema**: el campo se añade a `app/models.py` (`Mapped[...]`) y a los `BaseModel` de `app/main.py` que correspondan (`<Entidad>Out` siempre; `<Entidad>Create`/`<Entidad>Update` si el campo se puede escribir).
- **Validación**: si el campo tiene una regla de negocio (rango, formato, zona horaria), se declara con `@field_validator`, no se deja para que la base de datos la aplique.
- Ninguna de las tres capas se añade sin las otras dos en el mismo cambio — un campo en el modelo sin migración rompe el esquema real; un campo en el esquema sin validación deja pasar cualquier valor.
