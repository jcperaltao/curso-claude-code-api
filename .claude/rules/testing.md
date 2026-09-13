# Testing

## Dónde viven

- Todos los tests están en `tests/`, un archivo por recurso o por tipo de comprobación: `test_health.py`, `test_states_endpoint.py`, `test_projects_endpoint.py`, `test_tasks_endpoint.py`.
- El comportamiento de una migración (seed idempotente, `upgrade`/`downgrade`) vive en un archivo aparte del endpoint — `test_states_catalog.py`, no `test_states_endpoint.py` — aunque prueben el mismo recurso.
- Las fixtures compartidas (`api_client`, `db_session`, `postgres_schema`) viven solo en `tests/conftest.py`; ningún archivo de test las redefine.

## Cómo se nombran

- `test_<acción>_<sujeto>_<resultado_esperado>`, en español, nombrando el código HTTP o el efecto cuando aplica: `test_borrar_proyecto_con_tareas_devuelve_409`, `test_crear_tarea_con_titulo_vacio_devuelve_422`.
- Cada archivo de test (salvo `test_health.py`) abre con un docstring de módulo que dice, citando el nombre de la sección, qué parte de la Matriz Mínima de Tests cubre.

## Cómo se prepara y revierte la base de datos entre pruebas

- `postgres_schema` (fixture de sesión, en `conftest.py`) corre una vez por sesión de pytest: comprueba que Postgres responde y falla explícito si no (`pytest.fail`, nunca en silencio), y deja la base migrada desde vacío con `alembic downgrade base` + `alembic upgrade head`.
- Cada test individual recibe su propia conexión (`_connection`) con una transacción abierta antes del test y revertida (`rollback()`) al terminar, pase o falle el test.
- `api_client` y `db_session` comparten esa misma conexión mediante un *savepoint* propio (`join_transaction_mode="create_savepoint"`): lo que uno inserta lo ve el otro dentro del mismo test, y un `commit()` del endpoint no persiste de verdad en la base compartida.
- Ningún test deja filas en la base para el siguiente: la reversión es responsabilidad de la fixture, no de un `tearDown` manual en el test.

## Invariantes del contrato que no pueden faltar (Matriz Mínima de Tests, `docs/contrato-api.md`)

- Salud.
- CRUD feliz de proyectos y de tareas.
- IDs inexistentes.
- Título vacío y espacios ASCII (los invisibles Unicode son una regresión aparte).
- Proyecto o estado inexistente al crear una tarea.
- Borrado de proyecto con tareas (`409`).
- Filtros solos y combinados.
- Orden estable: dos llamadas idénticas devuelven los ids en la misma posición.
- Esquema de respuesta exacto: los campos declarados, ni uno más.
- Migración desde base vacía y rollback de la última revisión.
- El catálogo de estados existe tras migrar, y migrar dos veces no lo duplica.
- `due_at` omitido, válido, sin zona, vencido, futuro y tarea hecha.
- Los tests pueden añadir casos; no pueden debilitar estas invariantes.

## Aprendida a la fuerza

- Un test que prueba un fallo (un `404`, un `409`, un `422`) no se modifica ni se borra para que un cambio nuevo pase — si el comportamiento acordado cambió de verdad, se cambia `docs/contrato-api.md` primero, en un commit separado, y solo después el test. Así se hizo en este repositorio: al añadir `POST /tasks`, `test_borrar_proyecto_con_tareas_devuelve_409` (que insertaba la tarea directo en la sesión) no se tocó — se añadió `test_borrar_proyecto_con_tarea_creada_por_api_devuelve_409` al lado (`b067351`), y el original se quedó como estaba.
