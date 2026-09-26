"""Generic repository base.

Repositories are the only place that speaks SQLAlchemy. Services depend on
them, never on the ORM directly (invariant I2).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------- queries
    def _select(self) -> Any:
        """Base SELECT for this model.

        Typed as ``Any`` because SQLAlchemy changed ``Select``'s generic
        parameter between 2.0 and 2.1; repositories re-annotate their results.
        """
        return select(self.model)

    async def get(self, pk: Any) -> ModelT | None:
        return await self.session.get(self.model, pk)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        result = await self.session.scalars(self._select().limit(limit).offset(offset))
        rows: Sequence[ModelT] = result.all()
        return rows

    async def count(self) -> int:
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return int(result.scalar_one())

    # ------------------------------------------------------------ mutation
    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        return instance

    def add_all(self, instances: Sequence[ModelT]) -> None:
        self.session.add_all(list(instances))

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)

    async def delete_by_pk(self, pk: Any) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == pk))  # type: ignore[attr-defined]

    async def flush(self) -> None:
        await self.session.flush()
