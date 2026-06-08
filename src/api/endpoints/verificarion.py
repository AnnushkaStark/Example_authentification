from fastapi import APIRouter
from fastapi import status

from src.api.depends.auth import CurrentUserDepends
from src.api.depends.verification import VerificationServiceDepends
from src.constants.errors import ErrorCodes
from src.utils.errors import errs

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    responses=errs(
        e404=[
            ErrorCodes.EMAIL_NOT_FOUND,
            ErrorCodes.VERIFICATION_CODE_NOT_FOUND,
        ],
        e400=ErrorCodes.INVALID_VERIFICATION_CODE,
    ),
)
async def verify_user(
    code: str,
    current_user: CurrentUserDepends,
    service: VerificationServiceDepends,
):
    return await service.verify_user(
        code=code, user_id=current_user.id, user_uid=current_user.uid
    )


@router.post("/resend/", status_code=status.HTTP_200_OK)
async def resend_verification_code(
    current_user: CurrentUserDepends, service: VerificationServiceDepends
):
    return await service.resend_verification_code(
        user_email=current_user.email, user_id=current_user.id
    )
