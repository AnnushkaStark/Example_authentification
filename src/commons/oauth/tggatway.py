from dddshared.logger import log

from src.commons.base import ApiClientBase
from src.config.configs import app_settings
from src.config.configs import tg_api_gatway_settings


class TgGatwayClient(ApiClientBase):
    root_url = "https://gatewayapi.telegram.org/sendVerificationMessage"

    def _get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {tg_api_gatway_settings.GATWAY_KEY}"}

    async def send_tg_verification(self, code: str, phone: str) -> None:
        log.system.info("Отправка отп кода аутентификации")
        async with self._get_client(proxy=app_settings.TG_PROXY) as client:
            response = await client.post(
                self.root_url,
                json={
                    "phone_number": phone,
                    "code": code,
                    "code_length": len(code),
                    "ttl": 600,
                },
                headers=self._get_auth_headers(),
            )
            log.system.info(f"{response.json()}")
