from typing import Annotated

from authlib.jose import JoseError
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from fastapi import status
from fastapi_jwt import JwtAuthorizationCredentials
from pydantic import ValidationError

from src.api.depends.databse import Session
from src.commons.oauth.facebook import FacebookClient
from src.commons.oauth.google import GoogleClient
from src.commons.oauth.tg import TgClient
from src.commons.oauth.vk import VkClient
from src.commons.oauth.yandex import YandexClient
from src.commons.state import State
from src.constants.errors import ErrorCodes
from src.models import User
from src.repositories.blacklist import TokenBlacklistRepository
from src.repositories.user import UserRepository
from src.repositories.user_session import UserSessionRepository
from src.schemas.auth import TokenPayload
from src.security.security import access_security
from src.services.auth import AuthService


def get_facebook_client() -> FacebookClient:
    return FacebookClient()


FacebookClientDepends = Annotated[FacebookClient, Depends(get_facebook_client)]


def get_yandex_client() -> YandexClient:
    return YandexClient()


YandexClientDepends = Annotated[YandexClient, Depends(get_yandex_client)]


def get_google_client() -> GoogleClient:
    return GoogleClient()


GoogleClientDepends = Annotated[GoogleClient, Depends(get_google_client)]


def get_user_repo(session: Session) -> UserRepository:
    return UserRepository(session=session)


UserRepositoryDepends = Annotated[UserRepository, Depends(get_user_repo)]


def get_user_session_repo(session: Session) -> UserSessionRepository:
    return UserSessionRepository(session=session)


UserSessionRepositoryDepends = Annotated[
    UserSessionRepository, Depends(get_user_session_repo)
]


def get_token_blacklist_repo(session: Session) -> TokenBlacklistRepository:
    return TokenBlacklistRepository(session=session)


TokenBlacklistRepositoryDepends = Annotated[
    TokenBlacklistRepository, Depends(get_token_blacklist_repo)
]


def get_state() -> State:
    return State()


StateDepends = Annotated[State, Depends(get_state)]


def get_vk_client(state: StateDepends) -> VkClient:
    return VkClient(state=state)


VkClientDepends = Annotated[VkClient, Depends(get_vk_client)]


def get_tg_client(state: StateDepends) -> TgClient:
    return TgClient(state=state)


TgClientDepends = Annotated[TgClient, Depends(get_tg_client)]


def get_auth_service(
    user_repository: UserRepositoryDepends,
    user_session_repository: UserSessionRepositoryDepends,
    ynadex_client: YandexClientDepends,
    state: StateDepends,
    google_client: GoogleClientDepends,
    vk_client: VkClientDepends,
    tg_client: TgClientDepends,
    facebook_client: FacebookClientDepends,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        user_session_repository=user_session_repository,
        yandex_client=ynadex_client,
        state=state,
        google_client=google_client,
        vk_client=vk_client,
        tg_client=tg_client,
        facebook_client=facebook_client,
    )


AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]


Credentilals = Annotated[
    JwtAuthorizationCredentials, Security(access_security)
]


async def get_current_user(
    credentials: Credentilals,
    user_repository: UserRepositoryDepends,
    token_blackist_repository: TokenBlacklistRepositoryDepends,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.UNAUTHORIZED.value,
        )

    try:
        token_user = TokenPayload(**credentials.subject)
    except (JoseError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorCodes.COULD_NOT_VALIDATE_CREDENTIALS.value,
        ) from exc

    found_user = await user_repository.get_by_uid(uid=token_user.uid)
    if not found_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCodes.USER_NOT_FOUND.value,
        )

    if await token_blackist_repository.get_by_jti(jti=str(token_user.uid)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorCodes.YOU_DONT_NAVE_PERMISSION.value,
        )

    return found_user


UserDepends = Annotated[User, Depends(get_current_user)]
