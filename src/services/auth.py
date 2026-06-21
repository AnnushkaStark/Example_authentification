from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Literal

from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi_jwt import JwtAuthorizationCredentials
from ua_parser import user_agent_parser

from src.commons.oauth.google import GoogleClient
from src.commons.oauth.tg import TgClient
from src.commons.oauth.vk import VkClient
from src.commons.oauth.yandex import YandexClient
from src.commons.state import State
from src.config.configs import app_settings
from src.config.configs import jwt_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes
from src.models.user import User
from src.repositories.user import UserRepository
from src.repositories.user_session import UserSessionRepository
from src.schemas.auth import BaseRegister
from src.schemas.auth import TokenAccessRefresh
from src.schemas.auth import UserSessionBase
from src.security.password import hash_password
from src.security.password import verify_password
from src.security.password_generator import generate_password
from src.security.security import TokenSubject
from src.security.security import create_tokens
from src.security.verification import generate_veriify_code
from src.tasks import send_otp
from src.utils.logger import logger
from src.commons.oauth.facebook import FacebookClient


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_session_repository: UserSessionRepository,
        yandex_client: YandexClient,
        google_client: GoogleClient,
        vk_client: VkClient,
        tg_client: TgClient,
        state: State,
        facebook_client: FacebookClient
    ):
        self.user_repository = user_repository
        self.user_session_repository = user_session_repository
        self.yandex_client = yandex_client
        self.google_client = google_client
        self.vk_client = vk_client
        self.tg_client = tg_client
        self.state = state
        self.facebook_client = facebook_client

    async def _extract_clean_client_info(request: Request) -> dict:
        ip_address = (
            request.headers.get("X-Real-IP")
            or request.headers.get("X-Forwarded-For")
            or request.client.host
        )
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        raw_ua = request.headers.get("User-Agent", "Unknown")
        parsed_ua = user_agent_parser.Parse(raw_ua)

        os_name = parsed_ua["os"]["family"]
        browser_name = parsed_ua["user_agent"]["family"]

        device_family = parsed_ua["device"]["family"] or "Desktop"

        return {
            "ip": ip_address,
            "os": os_name,
            "browser": browser_name,
            "device": device_family,
            "raw_user_agent": raw_ua[:250],
        }

    async def _schema_validate(self, schema: BaseRegister) -> None:
        logger.info("Валидация данных пользователя")
        if await self.user_repository.get_by_email(email=schema.email):
            logger.warning("Элетронная почта уже зарегистрировна")
            raise DomainError(ErrorCodes.EMAIL_ALREADY_EXISTS)

        if await self.user_repository.get_by_phone_number(phone=schema.phone):
            logger.warning("Номер телефона уже зарегистрирован")
            raise DomainError(ErrorCodes.PHONE_NUMBER_ALREADY_EXISTS)

    async def register(self, schema: BaseRegister, request: Request) -> User:
        logger.info("Регитсрация пользователя")
        await self._schema_validate(schema=schema)
        schema.password = hash_password(password=schema.password)

        user = await self.user_repository.create(
            schema=schema,
            commit=False,
        )
        return user

    async def _create_user_session(
        self,
        uid: str,
        user_id: int,
        request: Request,
    ) -> dict[str, str]:
        session = await self.user_session_repository.create(
            schema=UserSessionBase(
                expired_at=datetime.now()
                + timedelta(minutes=jwt_settings.JWT_REFRESH_TOKEN_EXPIRES),
                user_id=user_id,
                client_info=self._extract_clean_client_info(request),
            ),
        )
        tokens = create_tokens(
            TokenSubject(
                uid=str(uid),
                jti=str(session.uid),
            ),
        )
        return tokens

    async def login_jwt(
        self, schema: BaseRegister, header: str, ip: str
    ) -> dict[str, str]:
        logger.info("Aутентификация пользователя")
        found_user = await self.user_repository.get_by_email(
            email=schema.email
        )
        if not found_user:
            logger.warning("Электронная почта не найдена")
            raise DomainError(ErrorCodes.EMAIL_NOT_FOUND)

        if not verify_password(
            plain_password=schema.password,
            hashed_password=found_user.password,
        ):
            raise DomainError(ErrorCodes.INVALID_PASSWORD)

        return await self._create_user_session(
            uid=str(found_user.uid),
            user_id=found_user.id,
            header=header,
        )

    async def refresh(
        self, credentials: JwtAuthorizationCredentials, request: Request
    ) -> dict[str, str]:
        logger.info("Обновление токена пользователя")
        found_session = await self.user_session_repository.get_by_uid(
            uid=credentials.subject["jti"]
        )
        if (
            not found_session
            or datetime.now(UTC) > found_session.expired_at
            or found_session.is_active is False
        ):
            logger.warning("Сессия пользователя не найдена")
            raise DomainError(ErrorCodes.UNAUTHORIZED)

        found_user = await self.user_repository.get_by_uid(
            credentials.subject["uid"]
        )
        if not found_user or not found_user.is_active:
            logger.warning("Пользователь не найден или заблокирован")
            raise DomainError(ErrorCodes.UNAUTHORIZED)

        await self.user_session_repository.partitial_update(
            uid=found_session.uid, new_value=False, value_name="is_active"
        )
        return await self._create_user_session(
            uid=found_user.uid, user_id=found_user.id, request=request
        )

    async def logout(
        self,
        credentials: JwtAuthorizationCredentials,
        mode: Literal["one_device", "all_device"],
    ):
        logger.info("Выход пользвтеля из системы")
        match mode:
            case "one_device":
                await self.user_session_repository.partitial_update(
                    uid=credentials.subject["jti"],
                    new_value=False,
                    value_name="is_active",
                )

            case "all_device":
                found_user = await self.user_repository.get_by_uid(
                    uid=credentials.subject.uid
                )
                if not found_user:
                    logger.error("пользователь не найден")
                    raise DomainError(ErrorCodes.USER_NOT_FOUND)
                await self.user_session_repository.deactivated_multi(
                    user_id=found_user.id
                )
        response = Response()
        response.delete_cookie(
            jwt_settings.ACCESS_TOKEN_COOKIE_KEY,
            path="/",
            secure=True,
            samesite="none",
        )
        response.delete_cookie(
            jwt_settings.REFRESH_TOKEN_COOKIE_KEY,
            path="/",
            secure=True,
            samesite="none",
        )

    async def _get_or_create(
        self,
        request: Request,
        phone: str | None = None,
        email: str | None = None,
    ) -> User:
        if email:  # noqa: SIM102
            if found_user := await self.user_repository.get_by_email(  # noqa: SIM102
                email=email
            ):
                return found_user

        if phone:  # noqa: SIM102
            if found_user := await self.user_repository.get_by_phone_number(  # noqa: SIM102
                phone=phone
            ):
                return found_user

        return await self.user_repository.create(
            schema=BaseRegister(
                email=email if email else None,
                phone_number=phone if phone else None,
                password=hash_password(generate_password()),
            ),
        )

    def _set_cokie(self, token_data: TokenAccessRefresh) -> None:
        response = RedirectResponse(app_settings.OAUTH_SUCESS_URL)
        response.set_cookie(
            key=jwt_settings.ACCESS_TOKEN_COOKIE_KEY,
            value=token_data.access_token,
            secure=True,
            samesite="none",
            path="/",
        )
        response.set_cookie(
            key=jwt_settings.REFRESH_TOKEN_COOKIE_KEY,
            value=token_data.refresh_token,
            secure=True,
            samesite="none",
            path="/",
        )
        return response

    async def _get_email_or_phone_oauth(
        self,
        code: str,
        media_type: Literal["vk", "yandex", "google", "tg", "facebook"],
        device_id: str | None = None,
        state: str | None = None,
    ) -> str:
        match media_type:
            case "google":
                return await self.google_client.get_email(code=code)

            case "yandex":
                return await self.yandex_client.get_email(code=code)

            case "vk":
                return await self.vk_client.get_email_or_phone(
                    code=code, state=state, device_id=device_id
                )
            case "tg":
                return await self.tg_client.get_user_phone(
                    code=code, state=state
                )
            case "facebook":
                return await self.facebook_client.get_email(code=code)

    async def oaut_media(
        self,
        code: str,
        request: Request,
        media_type: Literal["vk", "yandex", "google", "tg", "facebook"],
        device_id: str | None = None,
        state: str | None = None,
    ) -> dict[str, str]:
        email_or_phone = await self._get_email_or_phone_oauth(
            code=code, media_type=media_type, device_id=device_id, state=state
        )

        user = await self._get_or_create(
            email=email_or_phone if "@" in email_or_phone else None,
            request=request,
            phone=email_or_phone if "@" not in email_or_phone else None,
        )
        tokens = await self._create_user_session(
            uid=user.uid,
            user_id=user.id,
            request=request
        )
        return self._set_cokie(token_data=tokens)

    async def auth_otp(
        self, phone: str, mode: Literal["sms", "tg", "max"]
    ) -> None:
        logger.info("Авторизация по номеру телефона")
        if not await self.user_repository.get_by_phone_number(phone=phone):
            logger.warning("Номер телефона не найден")
            raise DomainError(ErrorCodes.PHONE_NOT_FOUND)

        code = generate_veriify_code()

        await self.state.set_state(key=code, value=phone)

        await send_otp.kiq(code=code, phone=phone, mode=mode)

    async def login_otp(
        self, code: str, request: Request
    ) -> dict[str, str]:
        logger.info("Проверка отп кода для создания сессии")
        found_number = await self.state.get_state(key=code)
        if not found_number:
            raise DomainError(ErrorCodes.VERIFICATION_CODE_NOT_FOUND)

        if found_user := await self.user_repository.get_by_phone_number(
            phone=found_number.decode("utf-8")
        ):
            return await self._create_user_session(
                uid=str(found_user.uid),
                user_id=found_user.id,
                request=request
            )
        logger.warning("Пользователь не найдне")
        raise DomainError(ErrorCodes.USER_NOT_FOUND)
