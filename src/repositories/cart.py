from dddshared.models.cart.cart import Cart
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository


class CartRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Cart)
