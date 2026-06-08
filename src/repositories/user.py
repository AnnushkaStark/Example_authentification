from dddshared.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, phone: str) -> User | None:
        result = await self.session.execute(
            select(self.model).where(self.model.phone_number == phone)
        )
        return result.scalar_one_or_none()
