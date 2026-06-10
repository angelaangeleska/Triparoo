from typing import Generic, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import Base, BaseRepository

ModelT = TypeVar("ModelT", bound=Base)


class GenericRepository(BaseRepository, Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        result = await self.session.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.execute(select(self.model).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
