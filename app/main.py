from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import State

app = FastAPI(title="TaskFlow API")


class StateOut(BaseModel):
    """Representación pública de un estado: exactamente ``id`` y ``code``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str


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
