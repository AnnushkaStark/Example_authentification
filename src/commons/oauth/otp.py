import time

from dddshared.logger import log

from src.commons.base import ApiClientBase
from src.config.configs import sms_settings
from src.constants.errors import DomainError
from src.constants.errors import ErrorCodes


class SmsClient(ApiClientBase):
    log.system.info("Отправка кода авторизации")
    root_url = "https://api.notificore.ru/v1.0/sms/create"

    def _get_auth_headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": f"{sms_settings.SMS_API_KEY}",
        }

    async def send_sms(self, code: str, phone: str) -> None:
        async with self._get_client() as client:
            response = await client.post(
                self.root_url,
                json={
                    "destination": "phone",
                    "originator": "NTF",
                    "body": f"Ваш код подтверждения {code}",
                    "msisdn": phone,
                    "reference": f"external_id{str(time.time())}",
                    "callback_url": sms_settings.SMS_CALLBACK_URL,
                },
                headers=self._get_auth_headers(),
            )
            log.system.info(response.text)
            if response.status_code != 200:
                log.system.error("Ошибка отправки кода авторизации")
                raise DomainError(ErrorCodes.ERROR_SEND_SMS)

            return response.json()
