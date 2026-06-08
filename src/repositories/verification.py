from dddshared.models.auth import VerificationCode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository


class VerificationCodeRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, VerificationCode)

    async def get_by_user_id_with_code(
        self, user_id: int, code: str
    ) -> VerificationCode | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.user_id == user_id, self.model.code == code
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> VerificationCode | None:
        result = await self.session.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()
