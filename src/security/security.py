from datetime import timedelta
from typing import TypedDict

from fastapi_jwt import JwtAccessBearerCookie
from fastapi_jwt import JwtRefreshBearer

from src.config.configs import jwt_settings
from src.schemas.auth import TokenAccessRefresh


class TokenSubject(TypedDict):
    uid: str
    jti: str


access_security = JwtAccessBearerCookie(
    secret_key=jwt_settings.JWT_SECRET_KEY,
    auto_error=False,
    access_expires_delta=timedelta(
        minutes=jwt_settings.JWT_ACCESS_TOKEN_EXPIRES
    ),
)
refresh_security = JwtRefreshBearer(
    secret_key=jwt_settings.JWT_SECRET_KEY,
    refresh_expires_delta=timedelta(
        minutes=jwt_settings.JWT_REFRESH_TOKEN_EXPIRES
    ),
    auto_error=False,
)


def create_tokens(subject: TokenSubject) -> TokenAccessRefresh:
    access_token = access_security.create_access_token(
        subject=subject,
        expires_delta=timedelta(minutes=jwt_settings.JWT_ACCESS_TOKEN_EXPIRES),
    )
    refresh_token = refresh_security.create_refresh_token(
        subject=subject,
        expires_delta=timedelta(
            minutes=jwt_settings.JWT_REFRESH_TOKEN_EXPIRES
        ),
    )

    return TokenAccessRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


ACCESS_TOKEN_COOKIE_KEY = jwt_settings.ACCESS_TOKEN_COOKIE_KEY
REFRESH_TOKEN_COOKIE_KEY = jwt_settings.REFRESH_TOKEN_COOKIE_KEY
