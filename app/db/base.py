from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BaseRepository:
    def __init__(self, session):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, instance: Any) -> Any:
        await self.session.refresh(instance)
        return instance
