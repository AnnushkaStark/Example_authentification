from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import UUID

from dddshared.models.base import Base
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession, model: Base):
        self.session = session
        self.model = model

    async def get_all(self) -> list[Base]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, schema: BaseModel, commit: bool = True) -> Base:
        result = await self.session.execute(
            insert(self.model)
            .values(schema.model_dump())
            .returning(self.model)
        )
        if commit:
            await self.session.commit()
        return result.scalar()

    async def create_bulk(self, schemas: list[BaseModel]) -> list[Base]:
        data = [s.model_dump() for s in schemas]
        objs = await self.session.execute(
            insert(self.model).values(data).returning(self.model)
        )
        await self.session.commit()
        return objs.scalars().all()

    async def remove(self, obj_id) -> None:
        await self.session.execute(
            delete(self.model).where(self.model.id == obj_id)
        )
        await self.session.commit()

    async def get_by_id(self, obj_id: int) -> Base | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar()

    async def get_by_uid(self, uid: UUID) -> Base | None:
        result = await self.session.execute(
            select(self.model).where(self.model.uid == uid)
        )
        return result.scalar()

    async def partitial_update(
        self, uid: UUID, new_value: Any, value_name: str, commit: bool = True
    ) -> None:
        obj = await self.get_by_uid(uid=uid)
        if obj:
            obj.__setattr__(value_name, new_value)

        if commit:
            await self.session.commit()

    async def remove_older_month(self) -> None:
        """
        Для модели сессий и блэклиста токенов
        """
        target_date = datetime.now() - timedelta(days=30)
        await self.session.execute(
            delete(self.model).where(self.model.created_at <= target_date)
        )
