from typing import Literal
from uuid import UUID

import sentry_sdk
from dddshared.models.enums import Locale
from pydantic import EmailStr
from taskiq import TaskiqMessage
from taskiq import TaskiqMiddleware
from taskiq import TaskiqResult
from taskiq import TaskiqScheduler
from taskiq_redis import ListRedisScheduleSource
from taskiq_redis import RedisAsyncResultBackend
from taskiq_redis import RedisStreamBroker

from src.commons.email_client import EmailClient
from src.commons.ip_info import IpIfoClient
from src.commons.oauth.otp import SmsClient
from src.commons.oauth.tggatway import TgGatwayClient
from src.config.configs import redis_settings
from src.config.configs import sentry_settings
from src.databases.pg import get_async_session
from src.repositories.blacklist import TokenBlacklistRepository
from src.repositories.user import UserRepository
from src.repositories.user_session import UserSessionRepository
from src.services.loaclization import LocalizationService

sentry_sdk.init(
    dsn=sentry_settings.AUTH_SENTRY_DNS,
    send_default_pii=True,
    enable_logs=True,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)


class SentryMiddleware(TaskiqMiddleware):
    def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        scope = sentry_sdk.get_current_scope()
        scope.set_tag("task_name", message.task_name)
        return message

    def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult
    ) -> None:
        if result.is_err:
            sentry_sdk.capture_exception(result.error)


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


@broker.task(task_name="send_mail")
async def send_mail(
    recepients: list[EmailStr],
    template_body: dict,
    subject: str = "",
    template: str = None,
) -> None:
    client = EmailClient()
    await client.send_mail(
        recepients=recepients,
        template_body=template_body,
        subject=subject,
        template=template,
        attachments=[],
    )


@broker.task(task_name="user_ip")
async def get_user_ip(
    request_headers: dict,
    user_uid: str,
) -> None:
    ip_info_client = IpIfoClient()
    service = LocalizationService(client=ip_info_client)
    user_locale = await service.get_localization(
        request_headers=request_headers
    )
    async for session in get_async_session():
        repo = UserRepository(session=session)
        await repo.partitial_update(
            new_value=Locale.KZ if user_locale == "KZ" else Locale.RU,
            uid=UUID(user_uid),
            value_name="country",
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
async def send_otp(
    code: str, phone: str, mode: Literal["tg", "sms", "max"]
) -> None:
    match mode:
        case "sms":
            client = SmsClient()
            await client.send_sms(code=code, phone=phone)

        case "tg":
            client = TgGatwayClient()
            await client.send_tg_verification(code=code, phone=phone)
