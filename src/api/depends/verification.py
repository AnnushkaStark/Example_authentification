from typing import Annotated

from fastapi import Depends

from src.api.depends.auth import UserRepositoryDepends
from src.api.depends.auth import VerificationRepositoryDepends
from src.services.verification import VerificationService


def get_verification_serivse(
    user_repository: UserRepositoryDepends,
    verification_repository: VerificationRepositoryDepends,
) -> VerificationService:
    return VerificationService(
        user_repository=user_repository,
        verification_repository=verification_repository,
    )


VerificationServiceDepends = Annotated[
    VerificationService, Depends(get_verification_serivse)
]
