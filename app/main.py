import unicodedata
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    WithJsonSchema,
    field_serializer,
    field_validator,
)
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Project, State, Task

app = FastAPI(title="TaskFlow API")

# Categorías Unicode sin carácter visible: control, formato y separadores de
# línea, párrafo y espacio. Un título que, tras recortar los extremos, solo
# contenga caracteres de estas categorías no deja nada visible.
_CATEGORIAS_INVISIBLES = {"Cc", "Cf", "Zl", "Zp", "Zs"}


def _normalizar_titulo(valor: str) -> str:
    """Recorta los extremos y rechaza un título sin ningún carácter visible."""

    recortado = valor.strip()
    if all(unicodedata.category(c) in _CATEGORIAS_INVISIBLES for c in recortado):
        raise ValueError("El título no puede estar vacío")
    return recortado


def _validar_due_at(valor: datetime | None) -> datetime | None:
    """Rechaza una fecha sin zona horaria: es ambigua y el contrato no la
    supone por su cuenta."""

    if valor is not None and valor.tzinfo is None:
        raise ValueError("due_at debe incluir zona horaria")
    return valor


class ErrorDetail(BaseModel):
    """Forma estable de un error de negocio: ``{"detail": "<mensaje>"}``."""

    detail: str


class StateOut(BaseModel):
    """Representación pública de un estado: exactamente ``id`` y ``code``."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(gt=0)]
    code: str


class ProjectOut(BaseModel):
    """Representación pública de un proyecto: ``id``, ``name`` y ``description``."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(gt=0)]
    name: str
    description: str | None


class ProjectCreate(BaseModel):
    """Cuerpo de entrada para crear un proyecto."""

    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Cuerpo de entrada para actualizar un proyecto: solo lo enviado cambia."""

    name: str | None = None
    description: str | None = None


class TaskOut(BaseModel):
    """Representación pública de una tarea (v2): incluye ``due_at``."""

    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(gt=0)]
    title: str
    description: str | None
    project_id: int
    state_id: int
    due_at: Annotated[
        datetime | None,
        WithJsonSchema(
            {"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]},
            mode="serialization",
        ),
    ]

    @field_serializer("due_at")
    def _serializar_due_at(self, valor: datetime | None) -> str | None:
        """Siempre en UTC, con ``Z`` y sin microsegundos."""

        if valor is None:
            return None
        return valor.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class TaskCreate(BaseModel):
    """Cuerpo de entrada para crear una tarea."""

    title: str
    description: str | None = None
    project_id: int
    state_id: int
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validar_title(cls, valor: str) -> str:
        return _normalizar_titulo(valor)

    @field_validator("due_at")
    @classmethod
    def _validar_due_at(cls, valor: datetime | None) -> datetime | None:
        return _validar_due_at(valor)


class TaskUpdate(BaseModel):
    """Cuerpo de entrada para actualizar una tarea: solo lo enviado cambia."""

    title: str | None = None
    description: str | None = None
    project_id: int | None = None
    state_id: int | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def _validar_title(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        return _normalizar_titulo(valor)

    @field_validator("due_at")
    @classmethod
    def _validar_due_at(cls, valor: datetime | None) -> datetime | None:
        return _validar_due_at(valor)


async def _get_project_or_404(
    project_id: int, session: AsyncSession
) -> Project:
    """Devuelve el proyecto o corta con 404 si no existe."""

    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


async def _get_state_or_404(state_id: int, session: AsyncSession) -> State:
    """Devuelve el estado o corta con 404 si no existe."""

    state = await session.get(State, state_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return state


async def _get_task_or_404(task_id: int, session: AsyncSession) -> Task:
    """Devuelve la tarea o corta con 404 si no existe."""

    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/states", response_model=list[StateOut])
async def list_states(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Sequence[State]:
    """Devuelve el catálogo de estados ordenado por ``position`` y ``id``."""

    result = await session.execute(select(State).order_by(State.position, State.id))
    return result.scalars().all()


@app.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(
    datos: ProjectCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Project:
    """Crea un proyecto y devuelve el recurso creado."""

    project = Project(name=datos.name, description=datos.description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Sequence[Project]:
    """Devuelve todos los proyectos existentes, ordenados por ``id`` ascendente."""

    result = await session.execute(select(Project).order_by(Project.id))
    return result.scalars().all()


@app.get(
    "/projects/{project_id}",
    response_model=ProjectOut,
    responses={404: {"model": ErrorDetail}},
)
async def get_project(
    project_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Project:
    """Devuelve un proyecto por id, o 404 si no existe."""

    return await _get_project_or_404(project_id, session)


@app.patch(
    "/projects/{project_id}",
    response_model=ProjectOut,
    responses={404: {"model": ErrorDetail}},
)
async def update_project(
    project_id: int,
    datos: ProjectUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Project:
    """Actualiza solo los campos enviados en el cuerpo, o 404 si no existe."""

    project = await _get_project_or_404(project_id, session)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(project, campo, valor)
    await session.commit()
    await session.refresh(project)
    return project


@app.delete(
    "/projects/{project_id}",
    status_code=204,
    responses={404: {"model": ErrorDetail}, 409: {"model": ErrorDetail}},
)
async def delete_project(
    project_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Borra un proyecto. 409 si tiene tareas, 404 si no existe, sin cascada."""

    project = await _get_project_or_404(project_id, session)
    tiene_tareas = await session.scalar(
        select(exists().where(Task.project_id == project_id))
    )
    if tiene_tareas:
        raise HTTPException(status_code=409, detail="El proyecto tiene tareas")
    await session.delete(project)
    await session.commit()


@app.post(
    "/tasks",
    response_model=TaskOut,
    status_code=201,
    responses={404: {"model": ErrorDetail}},
)
async def create_task(
    datos: TaskCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Task:
    """Crea una tarea. Valida que el proyecto y el estado referenciados existan."""

    await _get_project_or_404(datos.project_id, session)
    await _get_state_or_404(datos.state_id, session)

    task = Task(
        title=datos.title,
        description=datos.description,
        project_id=datos.project_id,
        state_id=datos.state_id,
        due_at=datos.due_at,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskOut])
async def list_tasks(
    session: Annotated[AsyncSession, Depends(get_session)],
    project_id: int | None = None,
    state_id: int | None = None,
    overdue: bool | None = None,
) -> Sequence[Task]:
    """Devuelve las tareas por ``id`` ascendente, filtrando por ``project_id``,
    ``state_id`` y/o ``overdue`` cuando se envían, solos o combinados.

    ``overdue=true`` exige ``due_at`` anterior al instante de evaluación y
    estado distinto de ``HECHA``; una tarea sin ``due_at`` nunca es vencida
    (la comparación con ``NULL`` no la deja pasar). Cualquier otro valor de
    ``overdue`` no aplica el filtro.
    """

    consulta = select(Task).order_by(Task.id)
    if project_id is not None:
        consulta = consulta.where(Task.project_id == project_id)
    if state_id is not None:
        consulta = consulta.where(Task.state_id == state_id)
    if overdue:
        ahora = datetime.now(UTC)
        consulta = consulta.join(State, State.id == Task.state_id).where(
            Task.due_at < ahora,
            State.code != "HECHA",
        )
    result = await session.execute(consulta)
    return result.scalars().all()


@app.get(
    "/tasks/{task_id}",
    response_model=TaskOut,
    responses={404: {"model": ErrorDetail}},
)
async def get_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Task:
    """Devuelve una tarea por id, o 404 si no existe."""

    return await _get_task_or_404(task_id, session)


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskOut,
    responses={404: {"model": ErrorDetail}},
)
async def update_task(
    task_id: int,
    datos: TaskUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Task:
    """Actualiza solo los campos enviados, validando proyecto y estado si cambian."""

    task = await _get_task_or_404(task_id, session)
    campos = datos.model_dump(exclude_unset=True)
    if "project_id" in campos:
        await _get_project_or_404(campos["project_id"], session)
    if "state_id" in campos:
        await _get_state_or_404(campos["state_id"], session)
    for campo, valor in campos.items():
        setattr(task, campo, valor)
    await session.commit()
    await session.refresh(task)
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    responses={404: {"model": ErrorDetail}},
)
async def delete_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Borra una tarea. 404 si no existe."""

    task = await _get_task_or_404(task_id, session)
    await session.delete(task)
    await session.commit()
