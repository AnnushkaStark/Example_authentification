from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from src.config.configs import redis_settings


@asynccontextmanager
async def get_redis() -> AsyncGenerator[Redis]:
    redis_client = Redis.from_url(redis_settings.REDIS_URL)
    yield redis_client
