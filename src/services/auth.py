import asyncio
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Literal

from dddshared.logger import log
from dddshared.models.enums import DeviceType
from dddshared.models.enums import Locale
from dddshared.models.user import User
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi_jwt import JwtAuthorizationCredentials
from user_agents import parse

from repositories.user_policy import UserPolicyRepository
from src.commons.ip_info import IpIfoClient
from src.commons.oauth.google import GoogleClient
from src.commons.oauth.tg import TgClient
from src.commons.oauth.vk import VkClient
from src.commons.oauth.yandex import YandexClient
from src.config.configs import app_settings
from src.config.configs import jwt_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes
from src.repositories.cart import CartRepository
from src.repositories.user import UserRepository
from src.repositories.user_session import UserSessionRepository
from src.repositories.verification import VerificationCodeRepository
from src.schemas import CartBase
from src.schemas.auth import BaseRegister
from src.schemas.auth import Register
from src.schemas.auth import TokenAccessRefresh
from src.schemas.auth import UserCreate
from src.schemas.auth import UserPolicyCreate
from src.schemas.auth import UserSessionBase
from src.schemas.auth import VerivficationCodeCreate
from src.security.password import hash_password
from src.security.password import verify_password
from src.security.password_generator import generate_password
from src.security.security import TokenSubject
from src.security.security import create_tokens
from src.security.verification import generate_veriify_code
from src.services.state import StateServise
from src.tasks import get_user_ip
from src.tasks import send_mail
from src.tasks import send_otp


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        user_session_repository: UserSessionRepository,
        verification_repository: VerificationCodeRepository,
        cart_repositry: CartRepository,
        user_policy_repository: UserPolicyRepository,
        yandex_client: YandexClient,
        state: StateServise,
        google_client: GoogleClient,
        vk_client: VkClient,
        tg_client: TgClient,
        ip_info_client: IpIfoClient,
    ):
        self.user_repository = user_repository
        self.cart_repository = cart_repositry
        self.user_policy_repository = user_policy_repository
        self.user_session_repository = user_session_repository
        self.verification_repository = verification_repository
        self.yandex_client = yandex_client
        self.state = state
        self.google_client = google_client
        self.vk_client = vk_client
        self.tg_client = tg_client
        self.ip_info_client = ip_info_client

    async def _schema_validate(self, schema: Register) -> None:
        log.app.info("Валидация данных пользователя")
        if await self.user_repository.get_by_email(email=schema.email):
            log.app.warning("Элетронная почта уже зарегистрировна")
            raise DomainError(ErrorCodes.EMAIL_ALREADY_EXISTS)

        if await self.user_repository.get_by_phone_number(
            phone=schema.phone_number
        ):
            log.app.warning("Номер телефона уже зарегистрирован")
            raise DomainError(ErrorCodes.PHONE_NUMBER_ALREADY_EXISTS)

    def _get_device_type(self, user_agent_string: str | None = None) -> str:
        if not user_agent_string:
            return DeviceType.UNKNOWN

        ua = parse(user_agent_string)

        if ua.is_mobile:
            return DeviceType.MOBILE

        if ua.is_tablet:
            return DeviceType.TABLET

        if ua.is_pc:
            return DeviceType.DESKTOP

        return DeviceType.UNKNOWN

    async def _get_ip_location(
        self, x_real_ip_string: str | None = None
    ) -> dict[str, str | None]:
        if not x_real_ip_string:
            return {"country": None, "city": None}
        return await self.ip_info_client.get_user_location(
            ip=x_real_ip_string.split(",")[0].strip()
        )

    async def _get_session_client_info(
        self,
        user_agent_string: str | None = None,
        x_real_ip_string: str | None = None,
    ) -> dict:
        ua = parse(user_agent_string) if user_agent_string else None

        location = await self._get_ip_location(
            x_real_ip_string=x_real_ip_string
        )

        return {
            "device": ua.device.family if ua else None,
            "os": ua.os.family if ua else None,
            "browser": ua.browser.family if ua else None,
            "country": location["country"],
            "city": location["city"],
        }

    async def register(self, schema: Register, request: Request) -> User:
        log.app.info("Регитсрация пользователя")
        await self._schema_validate(schema=schema)
        code = generate_veriify_code()
        schema.password = hash_password(password=schema.password)

        user = await self.user_repository.create(
            schema=UserCreate(
                **schema.model_dump(),
                is_verified=False,
            ),
            commit=False,
        )
        verification_code = await self.verification_repository.create(
            schema=VerivficationCodeCreate(
                code=code,
                user_id=user.id,
                expired_at=datetime.now() + timedelta(minutes=10),
            ),
            commit=False,
        )
        await self.cart_repository.create(
            schema=CartBase(user_id=user.id), commit=False
        )
        await self.user_policy_repository.create(
            schema=UserPolicyCreate(
                user_id=user.id,
                ip=request.headers.get("X-Real-Ip"),
                accepted=schema.accepted,
                document_version=schema.document_version,
            ),
            commit=False,
        )
        await self.cart_repository.session.commit()

        await get_user_ip.kiq(
            request_headers=dict(request.headers), user_uid=str(user.uid)
        )
        await send_mail.kiq(
            recepients=[user.email],
            template_body={
                "user_name": user.email,
                "verify_code": verification_code.code,
                "frontend_url": app_settings.FRONTEND_URL,
            },
            template="verification.html",
            subject="Код верификации 3D-outlet",
        )
        return user

    async def _create_user_session(
        self,
        uid: str,
        user_id: int,
        is_verified: bool,
        country: Locale | None = Locale.RU,
        header: str | None = None,
        ip: str | None = None,
    ) -> dict[str, str]:
        session = await self.user_session_repository.create(
            schema=UserSessionBase(
                device_type=self._get_device_type(user_agent_string=header),
                expired_at=datetime.now()
                + timedelta(minutes=jwt_settings.JWT_REFRESH_TOKEN_EXPIRES),
                user_id=user_id,
                client_info=await self._get_session_client_info(
                    user_agent_string=header, x_real_ip_string=ip
                ),
            )
        )
        tokens = create_tokens(
            TokenSubject(
                uid=str(uid),
                is_verified=is_verified,
                jti=str(session.uid),
                country=country.value if country else "RU",
            ),
        )
        return tokens

    async def login_jwt(
        self, schema: BaseRegister, header: str, ip: str
    ) -> dict[str, str]:
        log.app.info("Aутентификация пользователя")
        found_user = await self.user_repository.get_by_email(
            email=schema.email
        )
        if not found_user:
            log.app.warning("Электронная почта не найдена")
            raise DomainError(ErrorCodes.EMAIL_NOT_FOUND)

        if not verify_password(
            plain_password=schema.password,
            hashed_password=found_user.password,
        ):
            raise DomainError(ErrorCodes.INVALID_PASSWORD)

        return await self._create_user_session(
            uid=str(found_user.uid),
            is_verified=found_user.is_verified,
            user_id=found_user.id,
            header=header,
            country=found_user.country,
            ip=ip,
        )

    async def refresh(
        self, credentials: JwtAuthorizationCredentials, header: str, ip: str
    ) -> dict[str, str]:
        log.app.info("Обновление токена пользователя")
        found_session = await self.user_session_repository.get_by_uid(
            uid=credentials.subject["jti"]
        )
        if (
            not found_session
            or datetime.now(UTC) > found_session.expired_at
            or found_session.is_active is False
        ):
            log.app.warning("Сессия пользователя не найдена")
            raise DomainError(ErrorCodes.UNAUTHORIZED)

        found_user = await self.user_repository.get_by_uid(
            credentials.subject["uid"]
        )
        if not found_user or not found_user.is_active:
            log.app.warning("Пользователь не найден или заблокирован")
            raise DomainError(ErrorCodes.UNAUTHORIZED)

        await self.user_session_repository.partitial_update(
            uid=found_session.uid, new_value=False, value_name="is_active"
        )
        return await self._create_user_session(
            uid=found_user.uid,
            is_verified=found_user.is_verified,
            user_id=found_user.id,
            header=header,
            ip=ip,
        )

    async def logout(
        self,
        credentials: JwtAuthorizationCredentials,
        mode: Literal["one_device", "all_device"],
    ):
        log.app.info("Выход пользвтеля из системы")
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
                    log.app.error("пользователь не найден")
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

        user = await self.user_repository.create(
            schema=UserCreate(
                email=email if email else None,
                phone_number=phone if phone else None,
                password=hash_password(generate_password()),
                is_verified=True,
            ),
            commit=False,
        )
        await self.cart_repository.create(
            schema=CartBase(user_id=user.id), commit=False
        )
        await self.cart_repository.session.commit()
        await get_user_ip.kiq(headers=dict(request.headers), user_uid=user.uid)
        await asyncio.sleep(2.0)
        return user

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
        media_type: Literal["vk", "yandex", "google", "tg"],
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

    async def oaut_media(
        self,
        code: str,
        request: Request,
        media_type: Literal["vk", "yandex", "google", "tg"],
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
            is_verified=user.is_verified,
            country=user.country,
            header=request.headers.get("User-Agent"),
            ip=request.headers.get("X-Real-Ip"),
        )
        return self._set_cokie(token_data=tokens)

    async def auth_otp(
        self, phone: str, mode: Literal["sms", "tg", "max"]
    ) -> None:
        log.app.info("Авторизация по номеру телефона")
        if not await self.user_repository.get_by_phone_number(phone=phone):
            log.app.warning("Номер телефона не найден")
            raise DomainError(ErrorCodes.PHONE_NOT_FOUND)

        code = generate_veriify_code()

        await self.state.set_state(key=code, value=phone)

        await send_otp.kiq(code=code, phone=phone, mode=mode)

    async def login_otp(
        self, code: str, header: str, ip: str
    ) -> dict[str, str]:
        log.app.info("Проверка отп кода для создания сессии")
        found_number = await self.state.get_state(key=code)
        if not found_number:
            raise DomainError(ErrorCodes.OTP_NOT_FOUND)

        if found_user := await self.user_repository.get_by_phone_number(
            phone=found_number.decode("utf-8")
        ):
            return await self._create_user_session(
                uid=str(found_user.uid),
                is_verified=found_user.is_verified,
                user_id=found_user.id,
                country=found_user.country,
                header=header,
                ip=ip,
            )
        log.app.warning("Пользователь не найдне")
        raise DomainError(ErrorCodes.USER_NOT_FOUND)
