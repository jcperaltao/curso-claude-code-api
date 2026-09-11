---
name: planificar-incremento
description: Genera un plan de incrementos en docs/ para una capacidad nueva de TaskFlow, apoyado en el contrato, las decisiones de ingeniería y los comandos canónicos del repositorio. Úsala cuando se pida planificar, diseñar el enfoque de, o trazar los pasos de una funcionalidad nueva antes de tocar código. No implementa: no crea ni modifica código, no instala dependencias, no toca la base de datos.
---

# Planificar incremento

Genera el plan de una capacidad nueva de TaskFlow como una secuencia de
incrementos verificables, antes de escribir una sola línea de código.

## Fuentes contra las que se planifica

Lee estos documentos, en este orden, antes de proponer nada:

- `docs/contrato-api.md` — el comportamiento observable que el incremento
  debe alcanzar: códigos de estado, forma de la respuesta, orden,
  normalización, forma del error.
- `docs/decisiones-ingenieria.md` — las decisiones de ingeniería del equipo
  ya tomadas (persistencia, pruebas, datos locales); el plan las respeta, no
  las reabre.
- `README.md` — los comandos canónicos del repositorio; cada comprobación de
  un incremento se expresa con estos comandos, no con otros inventados.
- `CLAUDE.md` — restricciones del flujo de trabajo (PostgreSQL para
  persistencia, no debilitar tests, no tocar `.env`).
- El estado real del repositorio (código, tests y migraciones existentes),
  para no planificar sobre una versión desactualizada de lo que ya existe.

## Dónde y cómo se escribe el resultado

El plan se escribe como un archivo nuevo en `docs/`, nunca en la raíz, en
`tests/` ni junto al código. El nombre dice de qué es el plan:
`docs/plan-<tema>.md` (por ejemplo `docs/plan-proyectos.md`), siguiendo el
patrón ya usado por `docs/plan-persistencia.md`.

## Forma del plan

- Una sección **Fuentes** que enumera los documentos leídos.
- Una sección **Fuera de alcance** que nombra explícitamente qué no cubre
  este plan — no se deja implícito.
- Incrementos numerados (`Incremento 1`, `Incremento 2`, ...), cada uno con:
  - un objetivo concreto y acotado (un cambio que se pueda confirmar en un
    commit),
  - una sección **Comprobación** con un comando o secuencia de comandos
    ejecutable (de los comandos canónicos), nunca una descripción vaga como
    "verificar que funciona".

## Ninguna decisión queda aplazada

Si algo necesario para planificar no está decidido en
`docs/decisiones-ingenieria.md`, en `docs/contrato-api.md` ni en el resto del
repositorio, la skill se detiene y pregunta directamente — nunca lo redacta
en condicional ("se podría", "probablemente", "lo más razonable sería X o Y")
ni elige por su cuenta entre varias alternativas razonables. Una vez
respondida, la decisión se incorpora al plan como un hecho, no como una
hipótesis.

## Límite: planifica, no implementa

Esta skill solo produce el archivo de plan en `docs/`. No:

- crea ni modifica código de la aplicación o de los tests,
- instala ni añade dependencias,
- ejecuta migraciones ni toca la base de datos, ni siquiera para
  consultarla,
- ejecuta el linter ni la suite de tests.

Si ejecutar algo ayudaría a decidir, la skill lo señala como pregunta o como
parte del plan (un incremento futuro) — no lo hace ella misma.
