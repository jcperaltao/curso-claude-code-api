from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Project, State

app = FastAPI(title="TaskFlow API")


class StateOut(BaseModel):
    """Representación pública de un estado: exactamente ``id`` y ``code``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str


class ProjectOut(BaseModel):
    """Representación pública de un proyecto: ``id``, ``name`` y ``description``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
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


async def _get_project_or_404(
    project_id: int, session: AsyncSession
) -> Project:
    """Devuelve el proyecto o corta con 404 si no existe."""

    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


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
    """Devuelve los proyectos ordenados por ``id`` ascendente."""

    result = await session.execute(select(Project).order_by(Project.id))
    return result.scalars().all()


@app.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Project:
    """Devuelve un proyecto por id, o 404 si no existe."""

    return await _get_project_or_404(project_id, session)


@app.patch("/projects/{project_id}", response_model=ProjectOut)
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
