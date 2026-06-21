from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import status
from fastapi.requests import Request

from src.api.depends.auth import AuthServiceDepends
from src.api.depends.auth import Credentilals
from src.config.configs import google_settings
from src.config.configs import yandex_settings
from src.constants.errors import ErrorCodes
from src.schemas.auth import BaseRegister
from src.utils.errors import errs

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses=errs(
        e400=[
            ErrorCodes.EMAIL_ALREADY_EXISTS,
            ErrorCodes.PHONE_NUMBER_ALREADY_EXISTS,
        ]
    ),
)
async def create_user(
    schema: BaseRegister, service: AuthServiceDepends, request: Request
):
    return await service.register(schema=schema, request=request)


@router.post(
    "/login_jwt/",
    status_code=status.HTTP_200_OK,
    responses=errs(
        e404=ErrorCodes.EMAIL_NOT_FOUND, e400=ErrorCodes.INVALID_PASSWORD
    ),
)
async def login_jwt(
    schema: BaseRegister,
    service: AuthServiceDepends,
    user_agent: str | None = Header(None, alias="User-Agent"),
    x_real_ip: str | None = Header(None, alias="X-Real-IP"),
):
    return await service.login_jwt(
        schema=schema, header=user_agent, ip=x_real_ip
    )


@router.post(
    "/refresh/",
    status_code=status.HTTP_200_OK,
    responses=errs(e401=ErrorCodes.UNAUTHORIZED),
)
async def refresh(
    credentials: Credentilals,
    service: AuthServiceDepends,
    user_agent: str | None = Header(None, alias="User-Agent"),
    x_real_ip: str | None = Header(None, alias="X-Real-IP"),
):
    return await service.refresh(
        credentials=credentials, header=user_agent, ip=x_real_ip
    )


@router.post(
    "/logout/",
    status_code=status.HTTP_200_OK,
    responses=errs(e404=ErrorCodes.USER_NOT_FOUND),
    dependencies=[Depends(get_current_user)],
)
async def logout(
    credentials: Credentilals,
    service: AuthServiceDepends,
    mode: Literal["one_device", "all_device"],
):
    return await service.logout(credentials=credentials, mode=mode)


@router.get(
    "/",
)
async def yandex_auth_uri():
    return yandex_settings.get_redirect_uri()


@router.get(
    "/callback/",
    status_code=status.HTTP_200_OK,
)
async def yandex_callback(
    code: str, service: AuthServiceDepends, request: Request
):
    return await service.oaut_media(
        code=code, request=request, media_type="yandex"
    )


@router.get("/google/", status_code=status.HTTP_200_OK)
async def get_google_auth_uri():
    return google_settings.get_authorization_uri()


@router.get("/google/callback/", status_code=status.HTTP_200_OK)
async def get_google_callback(
    code: str, service: AuthServiceDepends, request: Request
):
    return await service.oaut_media(
        code=code, request=request, media_type="google"
    )


@router.get("/vk/", status_code=status.HTTP_200_OK)
async def get_auth_uri(service: AuthServiceDepends):
    return await service.vk_client.get_auth_uri()


@router.get("/vk/callback/", status_code=status.HTTP_200_OK)
async def get_vk_callback(
    code: str,
    state: str,
    device_id: str,
    service: AuthServiceDepends,
    request: Request,
):
    return await service.oaut_media(
        code=code,
        request=request,
        media_type="vk",
        device_id=device_id,
        state=state,
    )


@router.get("/tg/", status_code=status.HTTP_200_OK)
async def get_tg_uri(service: AuthServiceDepends):
    return await service.tg_client.get_auth_uri()


@router.get("/tg/callback/", status_code=status.HTTP_200_OK)
async def get_tg_callback(
    code: str,
    state: str,
    service: AuthServiceDepends,
    request: Request,
):
    return await service.oaut_media(
        code=code, state=state, request=request, media_type="tg"
    )


@router.post(
    "/auth_phone/",
    responses=errs(e404=ErrorCodes.PHONE_NOT_FOUND),
    status_code=status.HTTP_200_OK,
)
async def auth_phone(
    phone: str, service: AuthServiceDepends, mode: Literal["sms", "tg", "max"]
):
    return await service.auth_otp(phone=phone, mode=mode)


@router.post(
    "/verify_otp/",
    status_code=status.HTTP_200_OK,
    responses=errs(e404=[ErrorCodes.OTP_NOT_FOUND, ErrorCodes.USER_NOT_FOUND]),
)
async def verify_otp(
    code: str,
    service: AuthServiceDepends,
    user_agent: str | None = Header(None, alias="User-Agent"),
    x_real_ip: str | None = Header(None, alias="X-Real-IP"),
):
    return await service.login_otp(code=code, header=user_agent, ip=x_real_ip)


@router.get("/sms/callback/")
async def sms_callback(request: Request):
    return await request.body()
