from datetime import datetime

from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import UserSession
from src.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserSession)

    async def get_active_sessions(self, user_id: int) -> list[UserSession]:
        result = await self.session.execute(
            select(self.model).where(
                self.model.user_id == user_id,
                self.model.is_active.is_(True),
                self.model.expired_at >= datetime.now(),
            )
        )
        return result.scalars().all()

    async def deactivated_multi(self, user_id: int) -> None:
        await self.session.execute(
            update(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_active.is_(True),
                self.model.expired_at >= datetime.now(),
            )
            .values(is_active=False)
        )
        await self.session.commit()
