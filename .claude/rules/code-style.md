# Estilo de código

## Tipado

- Usa `X | None`, nunca `Optional[X]` ni `Union[X, None]` — ruff lo exige (UP007, UP045).
- `datetime.UTC`, nunca `datetime.timezone.utc` — ruff lo exige (UP017).
- Toda fecha es aware (con `tzinfo`): `datetime.now()`, `datetime.utcnow()` y `datetime.today()` están prohibidos — ruff lo exige (DTZ003, DTZ005).
- Cada módulo empieza con `from __future__ import annotations`.
- Ninguna función usa `Any`; el tipo se modela con una clase Pydantic o SQLAlchemy en su lugar (`grep -rn "Any" app/` no debe devolver nada).

## Esquemas frente a diccionarios sueltos

- Toda entrada y salida de un endpoint que expone datos del dominio es una clase `BaseModel` de Pydantic (`TaskOut`, `ProjectCreate`, ...), nunca un `dict` suelto — única excepción: `GET /health`.
- Un esquema de salida declara exactamente los campos que devuelve la API, ni uno más ni uno menos; no se usa `ConfigDict(extra=...)` para tolerar campos de sobra.
- Un modelo de SQLAlchemy no se devuelve nunca directo en una respuesta: siempre pasa por un `<Entidad>Out` con `model_config = ConfigDict(from_attributes=True)`.
- Un cuerpo de actualización parcial (`<Entidad>Update`) declara todos sus campos opcionales con default `None`, y el endpoint aplica solo `model_dump(exclude_unset=True)`.

## Funciones async

- Una función es `async def` si toca la sesión de base de datos o hace I/O; si es pura (validación, cálculo, composición de una cadena) es `def` normal.
- Ninguna llamada bloqueante dentro de una función `async def` — nada de `open()`, `subprocess` o `time.sleep()` — ruff lo exige (familia `ASYNC2xx`).
- Una dependencia de FastAPI que necesita otra se declara `Annotated[Tipo, Depends(func)]`, nunca `= Depends(func)` como valor por defecto — ruff prohibiría lo segundo (B008).
- Toda sesión de base de datos llega por `Depends(get_session)`; ninguna función abre su propia conexión fuera de `app/db.py`.

## Manejo de errores

- Un recurso inexistente se señaliza con `raise HTTPException(status_code=404, detail="<mensaje>")`, nunca devolviendo `None` o un valor sentinela.
- Un conflicto de negocio usa `HTTPException(status_code=409, detail=...)`, con el mismo patrón que el 404.
- Una entrada inválida se señaliza con `raise ValueError("<mensaje>")` dentro de un `@field_validator` de Pydantic, nunca con un `HTTPException(422, ...)` a mano.
- Ningún `except` desnudo ni ningún `except Exception:` que trague el error en silencio — ruff lo exige (E722, BLE001, S110, S112).
- Todo `HTTPException` lleva `detail` como cadena legible; nunca se lanza sin él.

## Lo que ruff ya exige hoy

- `pyproject.toml` no fija `select`: se usa el conjunto de reglas por defecto de ruff, no un subconjunto reducido — verifícalo con `ruff check --show-settings .`.
- Imports ordenados y sin uso muerto (`I001`, `F401`); variables sin usar, fuera (`F841`).
- `@lru_cache` sin paréntesis vacíos, nunca `@lru_cache()` (UP011).
- `x in dict`, nunca `x in dict.keys()` (SIM118).
- Nombre de módulo válido en snake_case (N999).
