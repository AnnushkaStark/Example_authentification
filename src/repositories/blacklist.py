from dddshared.models.auth import TokenBlacklist
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository


class TokenBlacklistRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TokenBlacklist)

    async def get_by_jti(self, jti: str) -> TokenBlacklist | None:
        result = await self.session.execute(
            select(self.model).where(self.model.jti == jti)
        )
        return result.scalar_one_or_none()
