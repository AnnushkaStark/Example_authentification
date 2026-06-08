from dddshared.logger import log

from src.config.configs import yandex_settings

from ..base import ApiClientBase


class YandexClient(ApiClientBase):
    token_url = "https://oauth.yandex.ru/token"  # noqa: S105
    user_info_url = "https://login.yandex.ru/info"

    async def get_email(self, code: str) -> dict[str, str]:
        log.app.info("Получение токена YandexID")
        async with self._get_client() as client:
            token_res = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": yandex_settings.YANDEX_CLIENT_ID,
                    "client_secret": yandex_settings.YANDEX_CLIENT_SECRET,
                },
            )
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            log.app.info("Получение информации о пользователе из YandexID")
            user_res = await client.get(
                self.user_info_url,
                headers={"Authorization": f"OAuth {access_token}"},
            )
            user_dict = user_res.json()
            return user_dict.get("default_email")
