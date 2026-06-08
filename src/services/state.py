from dddshared.logger import log
from redis.asyncio.lock import Lock

from src.databases.redis_db import get_redis


class StateServise:
    async def set_state(self, key: str, value: str, ttl: int = 600) -> None:
        log.system.info("Cохранение стейта кода в редис")

        async with get_redis() as redis:
            await redis.set(name=key, ex=ttl, value=value, nx=True)

    async def get_state(self, key: str) -> str | None:
        log.system.info("Проверка стейта")
        async with get_redis() as redis_client:
            if found_obj := await redis_client.get(key):
                log.system.info("Стейт найден")
                await redis_client.delete(key)
                return found_obj

            lock_key = f"{key}:lock"
            log.system.info("Стейта с блокировкой")
            async with Lock(
                redis_client, lock_key, timeout=10, blocking_timeout=15
            ):
                if found_obj := await redis_client.get(key):
                    log.system.info("Стейт найден")
                    return found_obj

                log.system.warning("Стейт неверный или устарел")
