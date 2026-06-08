from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.pg import get_async_session


async def get_db_connection() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


Session = Annotated[AsyncSession, Depends(get_db_connection)]
