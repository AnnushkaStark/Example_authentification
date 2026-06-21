from typing import Literal

from taskiq import TaskiqScheduler
from taskiq_redis import ListRedisScheduleSource
from taskiq_redis import RedisAsyncResultBackend
from taskiq_redis import RedisStreamBroker

from src.commons.oauth.otp import SmsClient
from src.commons.oauth.tggatway import TgGatwayClient
from src.config.configs import redis_settings
from src.databases.pg import get_async_session
from src.repositories.blacklist import TokenBlacklistRepository
from src.repositories.user_session import UserSessionRepository

broker = RedisStreamBroker(
    url=redis_settings.REDIS_URL, queue_name="auth:queue"
).with_result_backend(
    RedisAsyncResultBackend(redis_url=redis_settings.REDIS_URL)
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[
        ListRedisScheduleSource(url=redis_settings.REDIS_URL, prefix="auth")
    ],
)


async def _remove_old() -> None:
    async for session in get_async_session():
        blacklist_repo = TokenBlacklistRepository(session=session)
        session_repo = UserSessionRepository(session=session)
        await blacklist_repo.remove_older_month()
        await session_repo.remove_older_month()
        await session.commit()


@broker.task(schedule=[{"cron": "0 0 * * *"}], task_name="run_dayly_cleanup")
async def run_daily_cleanup():
    await _remove_old()


@broker.task(task_name="send_otp")
async def send_otp(code: str, phone: str, mode: Literal["tg", "sms"]) -> None:
    match mode:
        case "sms":
            client = SmsClient()
            await client.send_sms(code=code, phone=phone)

        case "tg":
            client = TgGatwayClient()
            await client.send_tg_verification(code=code, phone=phone)
