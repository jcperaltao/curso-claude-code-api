---
name: segmentar-commits
description: Divide el diff pendiente en el árbol de trabajo (ya implementado y verificado) en una secuencia de commits atómicos y ordenados, uno por capa o preocupación. Úsala cuando haya cambios sin commitear que mezclen varias capas (contrato, modelo+migración, endpoint+validación, tests) y quieras confirmarlos por separado en vez de en un único commit. No implementa nada nuevo: parte de código que ya existe en el árbol de trabajo.
---

# Segmentar commits

Toma el diff que ya existe, sin commitear, en el árbol de trabajo —código ya
escrito y verificado, no una tarea por implementar— y lo confirma como una
secuencia de commits pequeños y ordenados, cada uno con una sola
responsabilidad.

## Principio central: nunca reescribe código para simular un estado

El contenido final de cada archivo ya está en el árbol de trabajo y no
cambia. Lo único que varía entre un commit y el siguiente es **qué queda
registrado en el índice de git en ese momento**, y eso se consigue
exclusivamente con `git add`, completo o con `git add -p` (`git restore
--staged` para deshacer una selección, que tampoco toca el árbol de
trabajo):

- Si todo el diff de un archivo pertenece a un único commit del plan, se
  usa `git add <archivo>` completo.
- Si un mismo archivo mezcla cambios de más de una capa (por ejemplo, un
  ajuste de lint ajeno junto al campo nuevo), se seleccionan fragmentos con
  `git add -p <archivo>`.

Esta skill **no** edita código de aplicación ni de tests para reconstruir
una versión anterior o intermedia, y tampoco usa ningún comando que altere
el contenido del árbol de trabajo para aislar un estado —ni `git stash`, ni
`git checkout -- <archivo>`, ni `git restore <archivo>` sin `--staged`—: el
único mecanismo, en todo momento, es `git add`/`git add -p` sobre el índice.
Si un estado intermedio realmente no se puede expresar seleccionando
fragmentos del diff existente (dos capas entrelazadas línea a línea de forma
irreducible), se detiene y lo dice, en vez de fabricar una versión de
compromiso del código o de tocar el árbol de trabajo para simularlo.

## Orden de los commits

El orden no es arbitrario; sigue las fuentes de verdad del repositorio:

1. **Contrato primero, si cambia.** `CLAUDE.md` exige que
   `docs/contrato-api.md` se modifique en un commit separado, antes que
   tests o código, cuando el ticket cambia comportamiento observable. Si el
   diff toca el contrato, ese es siempre el primer commit, solo con ese
   archivo (y `docs/decisiones-ingenieria.md` si también cambió una decisión
   de ingeniería).
2. **Esquema de datos antes que lo que lo usa.** Modelo (`app/models.py`) y
   su migración de Alembic van juntos en un commit propio, antes que el
   endpoint que los consume — el mismo patrón que
   `feat: añade el modelo de Tarea y completa la tabla tasks para v1` o
   `feat: añade due_at a la tabla tasks` en el historial de este repositorio.
3. **Endpoint, validación y sus tests, juntos.** El código de `app/main.py`
   que expone o valida una capacidad va en el mismo commit que los tests que
   la ejercitan — nunca el test en un commit posterior dejando el anterior
   en rojo, ni el código sin ningún test que lo cubra. Sigue el patrón de
   `feat: añade POST /tasks` o `feat: añade due_at y el filtro overdue a la
   API de tareas`.
4. **Lo demás, en el commit que corresponda por tipo:** un plan nuevo en
   `docs/` es un commit `docs:` propio; un test que solo cierra un hueco de
   cobertura sin código nuevo es un commit `test:` propio (como
   `test: comprueba el 409 al borrar un proyecto con una tarea creada por la
   API`).

Cuando dos de estos grupos no tienen dependencia entre sí (por ejemplo, un
plan en `docs/` y una migración no relacionada), el orden entre ellos es
libre; cuando sí la tienen (modelo antes que endpoint, contrato antes que
código), se respeta.

## Invariante entre commits

Cada commit, tomado por separado, debe dejar el repositorio en un estado
consistente. Esto se garantiza **por construcción**, respetando el orden de
la sección anterior: el contrato no toca código; el modelo y la migración no
rompen ningún test existente por sí solos, porque nada los referencia
todavía; el endpoint llega siempre junto con los tests que lo prueban. No se
re-verifica ejecutando la suite entre un `git add` y el siguiente —el árbol
de trabajo no cambia de contenido en ningún momento de la segmentación (solo
el índice), así que ejecutar `pytest` a mitad de camino comprobaría el mismo
resultado final de siempre, no el estado aislado de ese commit; aislarlo de
verdad exigiría tocar el árbol de trabajo, que es justo lo que esta skill no
hace.

Lo que sí se ejecuta, sin tocar el árbol de trabajo, es la verificación
completa antes de empezar a segmentar (confirma la premisa de la skill: el
diff ya funciona) y otra vez al terminar el último commit (confirma que
segmentar no cambió el resultado):

```bash
uv run pytest -q
uv run ruff check .
```

Si alguno de los commits incluye una migración, se prueba también en los dos
sentidos, antes de empezar y después del último commit:

```bash
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
```

## Mensajes de commit

Mismo estilo que el resto del historial: una primera línea `tipo: resumen en
imperativo` (`feat:`, `test:`, `docs:`, `chore:`), seguida de un cuerpo que
explica **qué** cambia el commit y, si aplica, cuántos tests pasan tras él.
Las líneas de atribución (coautoría, sesión) se añaden o se omiten según lo
que ya declare `.claude/settings.json` en este repositorio — esta skill no
decide eso, lo hereda.

## Límite

Esta skill no escribe funcionalidad nueva ni corrige el código que segmenta.
Si al intentar dividir el diff aparece un fallo de test, de lint o de
migración que no estaba ahí antes de empezar, se detiene y lo reporta —no lo
arregla por su cuenta ni seguirá commiteando sobre un estado roto.
