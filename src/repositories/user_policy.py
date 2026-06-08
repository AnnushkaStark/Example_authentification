from dddshared.models import UserPolicyAgreement
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository


class UserPolicyRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserPolicyAgreement)
