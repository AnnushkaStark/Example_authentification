from typing import Annotated

from authlib.jose import JoseError
from dddshared.models.user import User
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from fastapi import status
from fastapi_jwt import JwtAuthorizationCredentials
from pydantic import ValidationError

from api.depends.localization import ApiInfoClentDepends
from repositories.user_policy import UserPolicyRepository
from src.api.depends.databse import Session
from src.commons.oauth.google import GoogleClient
from src.commons.oauth.tg import TgClient
from src.commons.oauth.vk import VkClient
from src.commons.oauth.yandex import YandexClient
from src.constants.errors import ErrorCodes
from src.repositories.blacklist import TokenBlacklistRepository
from src.repositories.cart import CartRepository
from src.repositories.user import UserRepository
from src.repositories.user_session import UserSessionRepository
from src.repositories.verification import VerificationCodeRepository
from src.schemas.auth import TokenPayload
from src.security.security import access_security
from src.services.auth import AuthService
from src.services.state import StateServise


def get_yandex_client() -> YandexClient:
    return YandexClient()


YandexClientDepends = Annotated[YandexClient, Depends(get_yandex_client)]


def get_google_client() -> GoogleClient:
    return GoogleClient()


GoogleClientDepends = Annotated[GoogleClient, Depends(get_google_client)]


def get_user_repo(session: Session) -> UserRepository:
    return UserRepository(session=session)


UserRepositoryDepends = Annotated[UserRepository, Depends(get_user_repo)]


def get_user_policy_repo(session: Session) -> UserPolicyRepository:
    return UserPolicyRepository(session=session)


UserPolicyRepositoryDepends = Annotated[
    UserPolicyRepository, Depends(get_user_policy_repo)
]


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


def get_verification_code_repo(session: Session) -> VerificationCodeRepository:
    return VerificationCodeRepository(session=session)


VerificationRepositoryDepends = Annotated[
    VerificationCodeRepository, Depends(get_verification_code_repo)
]


def get_cart_repo(session: Session) -> CartRepository:
    return CartRepository(session=session)


CartRepositryDepends = Annotated[CartRepository, Depends(get_cart_repo)]


def get_state_service() -> StateServise:
    return StateServise()


StateServiceDepends = Annotated[StateServise, Depends(get_state_service)]


def get_vk_client(state: StateServiceDepends) -> VkClient:
    return VkClient(state=state)


VkClientDepends = Annotated[VkClient, Depends(get_vk_client)]


def get_tg_client(state: StateServiceDepends) -> TgClient:
    return TgClient(state=state)


TgClientDepends = Annotated[TgClient, Depends(get_tg_client)]


def get_auth_service(
    user_repository: UserRepositoryDepends,
    user_session_repository: UserSessionRepositoryDepends,
    user_policy_repository: UserPolicyRepositoryDepends,
    verification_code_repository: VerificationRepositoryDepends,
    ynadex_client: YandexClientDepends,
    state: StateServiceDepends,
    google_client: GoogleClientDepends,
    vk_client: VkClientDepends,
    tg_client: TgClientDepends,
    cart_repository: CartRepositryDepends,
    ip_info_client: ApiInfoClentDepends,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        user_session_repository=user_session_repository,
        verification_repository=verification_code_repository,
        yandex_client=ynadex_client,
        state=state,
        google_client=google_client,
        vk_client=vk_client,
        tg_client=tg_client,
        cart_repositry=cart_repository,
        user_policy_repository=user_policy_repository,
        ip_info_client=ip_info_client,
    )


AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    user_repository: UserRepositoryDepends,
    token_blacklist_repository: TokenBlacklistRepositoryDepends,
    credentials: Annotated[
        JwtAuthorizationCredentials, Security(access_security)
    ],
) -> User | None:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.UNAUTHORIZED.value,
        )

    try:
        token_user = TokenPayload(**credentials.subject)
    except (JoseError, ValidationError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.UNAUTHORIZED.value,
        ) from err

    if await token_blacklist_repository.get_by_jti(token_user.jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.UNAUTHORIZED.value,
        )

    user = await user_repository.get_by_uid(uid=token_user.uid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCodes.UNAUTHORIZED.value,
        )

    return user


Credentilals = Annotated[
    JwtAuthorizationCredentials, Security(access_security)
]
CurrentUserDepends = Annotated[User, Depends(get_current_user)]
