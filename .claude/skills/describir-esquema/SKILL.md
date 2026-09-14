---
name: describir-esquema
description: Genera docs/esquema.md a partir del estado real de app/models.py y alembic/versions/ en el momento de invocarla: un diagrama de tablas y relaciones en Mermaid, más un diccionario de datos con una fila por columna (nombre, tipo, si admite nulos, y su significado cuando no es evidente). Úsala cuando se pida documentar, describir o diagramar el esquema de base de datos actual. No repite lo que ya fija docs/contrato-api.md: lo enlaza en vez de copiarlo. No modifica modelos, migraciones, el contrato ni la base de datos.
---

# Describir esquema

Documenta el esquema de base de datos tal como es **ahora**, leyendo el
código que lo define — nunca lo que un documento anterior dice que era, ni
lo que se supone que debería ser.

## Fuentes: el estado real, no lo asumido

Antes de escribir nada, en este orden:

1. **`app/models.py`, completo.** Es la declaración final y completa de
   cada tabla: `__tablename__`, cada `Mapped[...]` con su tipo Python, si
   la anotación admite `None` (nulidad), su `default` si lo tiene, y cada
   `ForeignKey` (de dónde sale la relación entre tablas).
2. **Cada archivo de `alembic/versions/`, completo, en el orden real de la
   cadena** — siguiendo `down_revision` desde la revisión sin padre hasta
   el head, nunca por fecha de modificación ni por nombre de archivo (dos
   migraciones de este repo comparten `mtime`). De ahí sale lo que
   `models.py` no dice: qué migración introdujo cada columna, las
   restricciones reales (`UniqueConstraint`, `ForeignKeyConstraint` y si
   lleva `ondelete`), el mecanismo del seed idempotente, y cualquier nota
   de docstring sobre un porqué que no es evidente solo con el tipo.
3. **`docs/contrato-api.md`, completo** — no para copiarlo, sino para
   saber con precisión qué apartado ya cubre qué recurso y poder enlazarlo
   por su título exacto en vez de reescribirlo.
4. Si ya existe `docs/esquema.md` de una ejecución anterior, su contenido
   **se descarta**: el archivo se regenera entero desde las fuentes de
   arriba, nunca se parte de él ni se fusiona con él.

Si lo que declara `app/models.py` para una tabla no coincide con lo que
produce aplicar las migraciones en orden (una columna en el modelo sin
migración que la cree, o al revés), la skill se detiene y lo reporta como
hallazgo — no decide cuál de las dos fuentes tiene razón, y no continúa
generando el resto del documento sobre una base contradictoria.

## Diagrama: Mermaid `erDiagram`

Va en un bloque ` ```mermaid ` dentro de `docs/esquema.md`. Es texto plano
(se versiona y se diferencia línea a línea en un commit como cualquier
otro archivo) y GitHub lo renderiza en la vista del repositorio sin ningún
plugin.

- Una entidad por tabla, con sus columnas y tipo abreviado; la clave
  primaria marcada `PK`.
- Cada relación con la cardinalidad real que impone la clave foránea
  encontrada en las migraciones: `||--o{` cuando la columna FK es
  `NOT NULL` ("un X tiene muchas Y, y toda Y requiere un X"), `|o--o{`
  cuando admite `NULL`.

## Diccionario de datos

Una tabla Markdown por tabla de la base, con esta forma exacta:

| Columna | Tipo | Nulo | Significado |
|---|---|---|---|

- **Tipo**: el tipo SQL real (el de la migración que lo crea), no el tipo
  Python de `models.py`.
- **Significado**: se deja vacío (`—`) cuando el nombre y el tipo ya lo
  dicen todo (`id`, `name`). Se rellena solo cuando no es evidente —por
  ejemplo, que `position` es el campo de orden del catálogo de estados, o
  que ninguna clave foránea lleva `ondelete`, así que el borrado con
  referencias también lo bloquea la base, no solo el endpoint.
- Si ese significado ya está explicado en `docs/contrato-api.md`, la fila
  enlaza a la sección exacta (`[ver contrato](../docs/contrato-api.md#...)`)
  en vez de reexplicarlo.

## No duplicar el contrato

`docs/contrato-api.md` ya fija comportamiento observable: códigos de
estado, forma de la respuesta, reglas de validación. `docs/esquema.md` no
repite nada de eso — describe la base de datos, no la API. Ejemplo: el
contrato dice que borrar un proyecto con tareas responde `409`; el
diccionario de datos no repite ese `409`, pero sí dice que la FK
`tasks.project_id → projects.id` no tiene `ondelete`, con un enlace a la
sección del contrato para quien quiera el porqué de negocio.

## Salida

Un único archivo: `docs/esquema.md`, con las dos secciones de arriba
(Diagrama, Diccionario de datos). Se sobrescribe entero en cada
ejecución — no es un archivo que se edita a mano entre ejecuciones.

## Límite: describe, no modifica

Esta skill no:

- crea, edita ni sugiere cambios en `app/models.py` ni en
  `alembic/versions/`,
- crea una migración nueva, aunque encuentre una discrepancia (la reporta,
  no la corrige),
- toca `docs/contrato-api.md`,
- se conecta a la base de datos, ni siquiera para consultarla de solo
  lectura — toda la información sale de leer los archivos `.py`,
- ejecuta ningún comando de los que fija `README.md`: se limita a leer las
  fuentes de arriba y escribir `docs/esquema.md`.
