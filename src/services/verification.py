from datetime import datetime
from datetime import timedelta
from uuid import UUID

from dddshared.logger import log

from src.config.configs import app_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes
from src.repositories.user import UserRepository
from src.repositories.verification import VerificationCodeRepository
from src.schemas.auth import VerivficationCodeCreate
from src.security.verification import generate_veriify_code
from src.tasks import send_mail


class VerificationService:
    def __init__(
        self,
        user_repository: UserRepository,
        verification_repository: VerificationCodeRepository,
    ):
        self.user_repository = user_repository
        self.verification_repository = verification_repository

    async def verify_user(
        self, code: str, user_id: int, user_uid: UUID
    ) -> None:
        log.app.info("Верификация пользователя")
        found_code = (
            await self.verification_repository.get_by_user_id_with_code(
                user_id=user_id, code=code
            )
        )
        if not found_code:
            log.app.warning("Пользователь не найден")
            raise DomainError(ErrorCodes.VERIFICATION_CODE_NOT_FOUND)

        if found_code.expired_at.replace(
            tzinfo=None
        ) <= datetime.now().replace(tzinfo=None):
            log.app.info("Неверный код верефикации")
            raise DomainError(ErrorCodes.INVALID_VERIFICATION_CODE)

        await self.user_repository.partitial_update(
            uid=user_uid, new_value=True, value_name="is_verified"
        )

    async def resend_verification_code(
        self, user_email: str, user_id: int
    ) -> None:
        log.app.info("Повторная отправка кода верификации")
        found_code = await self.verification_repository.get_by_user_id(
            user_id=user_id
        )
        if found_code:
            await self.verification_repository.remove(obj_id=found_code.id)

        code = generate_veriify_code()
        await self.verification_repository.create(
            schema=VerivficationCodeCreate(
                code=code,
                expired_at=datetime.now() + timedelta(minutes=10),
                user_id=user_id,
            )
        )
        await send_mail.kiq(
            recepients=[user_email],
            template_body={
                "user_name": user_email,
                "verify_code": code,
                "frontend_url": app_settings.FRONTEND_URL,
            },
            template="verification.html",
            subject="Код верификации 3D-outlet",
        )
        return "Ok"
