import secrets

from dddshared.logger import log

from src.commons.base import ApiClientBase
from src.config.configs import vk_settings
from src.services.state import StateServise


class VkClient(ApiClientBase):
    def __init__(self, state: StateServise):
        self.state = state
        self.root_url = "https://id.vk.ru/authorize"
        self.token_url = "https://id.vk.ru/oauth2/auth"
        self.user_data_url = "https://id.vk.ru/oauth2/public_info"

    async def get_auth_uri(self) -> dict[str, str]:
        code_verifier, code_challenge = self._generate_pkce_pair()

        state = secrets.token_urlsafe(32)
        await self.state.set_state(
            key=f"vk_auth:{state}", value=code_verifier, ttl=600
        )

        return self._generate_redirect_uri(
            scope="email, phone",
            client_code=vk_settings.APP_ID,
            redirect_uri=vk_settings.VK_CALLBACK_URL,
            state=state,
            code_challenge=code_challenge,
            auth_url=self.root_url,
        )

    async def get_email_or_phone(
        self, code: str, state: str, device_id: str
    ) -> str:
        code_verifier = await self.state.get_state(key=f"vk_auth:{state}")
        if not code_verifier:
            log.app.error(
                f"Верификатор для state {state} не найден или просрочен"
            )
            return None
        clean_verifier = (
            code_verifier.decode("utf-8")
            if isinstance(code_verifier, bytes)
            else code_verifier
        )
        payload = {
            "grant_type": "authorization_code",
            "code_verifier": clean_verifier,
            "redirect_uri": vk_settings.VK_CALLBACK_URL,
            "code": code,
            "client_id": vk_settings.APP_ID,
            "device_id": device_id,
        }

        async with self._get_client() as client:
            response = await client.post(self.token_url, data=payload)
            log.app.info(f"{response.json()}")
            token_id = response.json()["id_token"]
            payload = {"client_id": vk_settings.APP_ID, "id_token": token_id}
            response = await client.post(self.user_data_url, data=payload)

            log.app.info(f"{response.json()}")
            email = response.json().get("user", {}).get("email", "")
            if email != "":
                return email

            phone = response.json().get("user", {}).get("phone", "")
            if phone != "":
                return phone
